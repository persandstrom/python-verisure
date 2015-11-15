"""
API to communicate with Verisure mypages
"""

import requests
import re

# this import is depending on python version
try:
    import HTMLParser
    UNESCAPE = HTMLParser.HTMLParser().unescape
except ImportError:
    import html
    UNESCAPE = html.unescape


class Error(Exception):
    ''' mypages error '''
    pass


class LoginError(Error):
    ''' login failed '''
    pass


class ResponseError(Error):
    ''' Unexcpected response '''
    pass


class MyPages(object):
    """ Interface to verisure MyPages

    Args:
        username (str): Username used to log in to mypages
        password (str): Password used to log in to mypages
    """

    DEVICE_ALARM = 'alarm'
    DEVICE_CLIMATE = 'climate'
    DEVICE_ETHERNET = 'ethernet'
    DEVICE_HEATPUMP = 'heatpump'
    DEVICE_MOUSEDETECTION = 'mousedetection'
    DEVICE_SMARTCAM = 'smartcam'
    DEVICE_SMARTPLUG = 'smartplug'
    DEVICE_VACATIONMODE = 'vacationmode'

    ALL_DEVICES = [
        DEVICE_ALARM, DEVICE_CLIMATE, DEVICE_ETHERNET, DEVICE_HEATPUMP,
        DEVICE_MOUSEDETECTION, DEVICE_SMARTCAM, DEVICE_SMARTPLUG,
        DEVICE_VACATIONMODE,
        ]

    SMARTPLUG_ON = 'on'
    SMARTPLUG_OFF = 'off'
    ALARM_ARMED_HOME = 'ARMED_HOME'
    ALARM_ARMED_AWAY = 'ARMED_AWAY'
    ALARM_DISARMED = 'DISARMED'

    DOMAIN = 'https://mypages.verisure.com'
    URL_LOGIN = DOMAIN + '/j_spring_security_check?locale=en_GB'
    URL_START = DOMAIN + '/uk/start.html'

    OVERVIEW_URL = {
        DEVICE_ALARM: DOMAIN + '/remotecontrol',
        DEVICE_CLIMATE: DOMAIN + '/overview/climatedevice',
        DEVICE_ETHERNET: DOMAIN + '/overview/ethernetstatus',
        DEVICE_HEATPUMP: DOMAIN + '/overview/heatpump',
        DEVICE_MOUSEDETECTION: DOMAIN + '/overview/mousedetection',
        DEVICE_SMARTCAM: DOMAIN + '/overview/smartcam',
        DEVICE_SMARTPLUG: DOMAIN + '/overview/smartplug',
        DEVICE_VACATIONMODE: DOMAIN + '/overview/vacationmode',
        }

    COMMAND_URL = {
        DEVICE_ALARM: DOMAIN + '/remotecontrol/armstatechange.cmd',
        DEVICE_SMARTPLUG: DOMAIN + '/smartplugs/onoffplug.cmd'
        }

    CHECK_ALARM_STATE = DOMAIN + '/remotecontrol/checkstate.cmd'

    RESPONSE_TIMEOUT = 3

    CSRF_REGEX = re.compile(
        r'\<input type="hidden" name="_csrf" value="' +
        r'(?P<csrf>([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}))' +
        r'" /\>')

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session = None
        self._csrf = ''

    def __enter__(self):
        """ Enter context manager, open session """
        self.login()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """ Exit context manager, close session """
        self.logout()

    def login(self):
        """ Login to mypages

        Login before calling any read or write commands

        """
        self._session = requests.Session()
        auth = {
            'j_username': self._username,
            'j_password': self._password
            }
        req = requests.Request(
            'POST',
            MyPages.URL_LOGIN,
            cookies=dict(self._session.cookies),
            data=auth
            ).prepare()
        response = self._session.send(req, timeout=MyPages.RESPONSE_TIMEOUT)
        validate_response(response)
        status = _json_to_dict(response.text)
        if not status['status'] == 'ok':
            raise LoginError(status['message'])

    def logout(self):
        """ Ends session

        note:
            Ends the session, will not call the logout command on mypages

        """
        self._session.close()
        self._session = None

    def _read_status(self, overview_type):
        """ Read all statuses of a device type """

        self._ensure_session()
        url = MyPages.OVERVIEW_URL[overview_type]
        response = self._session.get(url)
        status = _json_to_dict(response.text)
        if isinstance(status, list):
            return [Overview(overview_type, val) for val in status]
        return [Overview(overview_type, status)]

    def get_overview(self, overview):
        """ Read overview of a device type from mypages

            Args:
                overview (str): 'alarm', 'climate', 'ethernet', 'heatpump',
                                'mousedetection', 'smartcam', 'smartplug',
                                or 'vacationmode'

                Returns: An array of overviews for the selected device type

        """

        if overview not in MyPages.ALL_DEVICES:
            raise Error('overview {} not recognised'.format(
                overview))
        return self._read_status(overview)

    def get_overviews(self):
        """ Read overviews of all device types from mypages
            Returns: An array of overviews for all device types

        """

        overviews = []
        for device in self.ALL_DEVICES:
            overviews.extend(self._read_status(device))
        return overviews

    def wait_while_pending(self, max_request_count=100):
        """ Wait for pending alarm to finish

            Args:
                max_request_count (int): maximum number of post requests

            Returns: True if success eler False

        """

        for counter in range(max_request_count):
            data = {'counter': counter}
            response = _json_to_dict(self._post(self.CHECK_ALARM_STATE, data))
            if 'hasResult' not in response:
                break
            if 'hasPending' not in response:
                return True
            counter = counter + 1
        return False

    def set_smartplug_status(self, device_id, value):
        """ set status of a smartplug component

            Args:
                device_id (str): smartplug device id
                value (str): 'on' or 'off'

        """

        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        self._post(MyPages.COMMAND_URL[MyPages.DEVICE_SMARTPLUG], data)

    def set_alarm_status(self, code, state):
        """ set status of alarm component

            Args:
                code (str): Personal alarm code (four digits)
                state (str): 'ARMED_HOME', 'ARMED_AWAY' or 'DISARMED'

        """
        data = {
            'code': code,
            'state': state
            }
        self._post(MyPages.COMMAND_URL[MyPages.DEVICE_ALARM], data)

    def _post(self, url, data):
        """ set status of a component """

        self._ensure_session()
        req = requests.Request(
            'POST',
            url,
            cookies=dict(self._session.cookies),
            headers={'X-CSRF-TOKEN': self._get_csrf()},
            data=data
            ).prepare()
        response = self._session.send(
            req,
            timeout=MyPages.RESPONSE_TIMEOUT)
        validate_response(response)
        return response.text

    def _get_csrf(self):
        """ Retreive X-CSRF-TOKEN from start.html """

        response = self._session.get(
            MyPages.URL_START,
            timeout=MyPages.RESPONSE_TIMEOUT)
        validate_response(response)
        match = MyPages.CSRF_REGEX.search(response.text)
        return match.group('csrf')

    def _ensure_session(self):
        ''' ensures that a session is created '''

        if not self._session:
            raise Error('Session not started')


# pylint: disable=W0612,W0123
def _json_to_dict(json):
    ''' transform json with unicode characters to dict '''

    true, false, null = True, False, None
    return eval(UNESCAPE(json))


def validate_response(response):
    """ Verify that response is OK """

    if response.status_code != 200:
        raise ResponseError(
            'status code: {} - {}'.format(
                response.status_code,
                response.text))


class Overview(object):
    ''' mypages device overview

        Note: Not ment to be instansiated from outside of this module

        Args:
            overview_type (str): Type of device
            status (str): the json returned from mypages

    '''

    def __init__(self, overview_type, status):
        self.__dict__.update(status)
        self._overview_type = overview_type

    def get_typename(self):
        """ get the type of device

            Returns (str): name of the device type

        """

        return self._overview_type

    def get_status(self):
        ''' get all status items as a dict

            Returns (dict): All status items as a dict

        '''

        return [(key, value) for (key, value)
                in self.__dict__.items() if not key.startswith('_')]
