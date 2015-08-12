"""
API to communicate with mypages
"""

import requests
import re

DEVICE_ALARM = 'alarm'
DEVICE_CLIMATE = 'climate'
DEVICE_ETHERNET = 'ethernet'
DEVICE_HEATPUMP = 'heatpump'
DEVICE_MOUSEDETECTION = 'mousedetection'
DEVICE_SMARTCAM = 'smartcam'
DEVICE_SMARTPLUG = 'smartplug'
DEVICE_VACATIONMODE = 'vacationmode'

SMARTPLUG_ON = 'on'
SMARTPLUG_OFF = 'off'
ALARM_ARMED_HOME = 'ARMED_HOME'
ALARM_ARMED_AWAY = 'ARMED_AWAY'
ALARM_DISARMED = 'DISARMED'

# this import is depending on python version
try:
    import HTMLParser
    UNESCAPE = HTMLParser.HTMLParser().unescape
except ImportError:
    import html
    UNESCAPE = html.unescape

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


def get_overviews():
    ''' return a list of avalible overviews '''
    return OVERVIEW_URL.keys()

COMMAND_URL = {
    DEVICE_ALARM: DOMAIN + '/remotecontrol/armstatechange.cmd',
    DEVICE_SMARTPLUG: DOMAIN + '/smartplugs/onoffplug.cmd'
    }

RESPONSE_TIMEOUT = 3

CSRF_REGEX = re.compile(
    r'\<input type="hidden" name="_csrf" value="' +
    r'(?P<csrf>([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}))' +
    r'" /\>')


class Error(Exception):
    ''' mypages error '''
    pass


class MyPages(object):
    """ Interface to verisure MyPages """

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
        """ Login to mypages """
        self._session = requests.Session()
        auth = {
            'j_username': self._username,
            'j_password': self._password
            }
        req = requests.Request(
            'POST',
            URL_LOGIN,
            cookies=dict(self._session.cookies),
            data=auth
            ).prepare()
        response = self._session.send(req, timeout=RESPONSE_TIMEOUT)
        validate_response(response)

    def logout(self):
        """ Ends session """
        self._session.close()
        self._session = None

    def _read_status(self, overview_type):
        """ Read all statuses of a device type """
        if not self._session:
            raise ConnectionError('Not logged in')
        url = OVERVIEW_URL[overview_type]
        response = self._session.get(url)
        true, false = True, False
        status = eval(UNESCAPE(response.text))
        if isinstance(status, list):
            return [Overview(overview_type, val) for val in status]
        return Overview(overview_type, status)

    def get_overview(self, overview):
        ''' Read overview from mypages '''
        if overview not in get_overviews():
            raise Error('overview {} not recognised'.format(
                overview))
        return self._read_status(overview)

    def set_smartplug_status(self, device_id, value):
        """ set status of a smartplug component (on, off) """
        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        self._set_status(COMMAND_URL['smartplug'], data)

    def set_alarm_status(self, code, state):
        """ set status of alarm component """
        data = {
            'code': code,
            'state': state
            }
        self._set_status(COMMAND_URL['alarm'], data)

    def _set_status(self, url, data):
        """ set status of a component """
        req = requests.Request(
            'POST',
            url,
            cookies=dict(self._session.cookies),
            headers={'X-CSRF-TOKEN': self._get_csrf()},
            data=data
            ).prepare()
        response = self._session.send(req, timeout=RESPONSE_TIMEOUT)
        validate_response(response)
        return response.text

    def _get_csrf(self):
        """ Retreive X-CSRF-TOKEN from start.html """
        response = self._session.get(URL_START, timeout=RESPONSE_TIMEOUT)
        validate_response(response)
        match = CSRF_REGEX.search(response.text)
        return match.group('csrf')


def validate_response(response):
    """ Verify that response is OK """
    if response.status_code != 200:
        raise ConnectionError(
            'status code: {} - {}'.format(
                response.status_code,
                response.text))


class Overview(object):
    ''' mypages device overview '''
    def __init__(self, overview_type, status):
        self.__dict__.update(status)
        self._overview_type = overview_type

    def get_typename(self):
        ''' name of the overview type '''
        return self._overview_type

    def get_status(self):
        ''' return all status items as a list '''
        return [(key, value) for (key, value)
                in self.__dict__.items() if not key.startswith('_')]
