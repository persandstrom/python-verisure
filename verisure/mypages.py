"""
API to communicate with mypages
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

DOMAIN = 'https://mypages.verisure.com'
URL_LOGIN = DOMAIN + '/j_spring_security_check?locale=en_GB'
URL_ALARM_STATUS = DOMAIN + '/remotecontrol'
URL_CLIMATE_STATUS = DOMAIN + '/overview/climatedevice'
URL_SMARTPLUG_STATUS = DOMAIN + '/overview/smartplug'
URL_ETHERNET_STATUS = DOMAIN + '/overview/ethernetstatus'
URL_START = DOMAIN + '/uk/start.html'
URL_SMARTPLUG_ONOFF_CMD = DOMAIN + '/smartplugs/onoffplug.cmd'
URL_ALARM_STATE_CHANGE_CMD = DOMAIN + '/remotecontrol/armstatechange.cmd'
RESPONSE_TIMEOUT = 3

CSRF_REGEX = re.compile(
    r'\<input type="hidden" name="_csrf" value="' +
    r'(?P<csrf>([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}))' +
    r'" /\>')


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

    def _read_status(self, device_status, url):
        """ Read all statuses of a device type """
        if not self._session:
            raise ConnectionError('Not logged in')
        response = self._session.get(url)
        true, false = True, False
        status_array = eval(UNESCAPE(response.text))
        return [device_status(status) for status in status_array]

    def get_alarm_status(self):
        """ Get status from alarm devices """
        return self._read_status(Alarm, URL_ALARM_STATUS)

    def get_climate_status(self):
        """ Get status from climate devices """
        return self._read_status(Climate, URL_CLIMATE_STATUS)

    def get_smartplug_status(self):
        """ Get status of smartplug devices """
        return self._read_status(Smartplug, URL_SMARTPLUG_STATUS)

    def get_ethernet_status(self):
        """ Get status of ethernet devices """
        return self._read_status(Ethernet, URL_ETHERNET_STATUS)

    def set_smartplug_status(self, device_id, value):
        """ set status of a smartplug component (on, off) """
        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        self._set_status(URL_SMARTPLUG_ONOFF_CMD, data)

    def set_alarm_status(self, code, state):
        """ set status of alarm component """
        data = {
            'code': code,
            'state': state
            }
        self._set_status(URL_ALARM_STATE_CHANGE_CMD, data)

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


class Device(object):
    ''' Baseclass for mypages devices '''
    def __init__(self, status):
        self.__dict__.update(status)


class Ethernet(Device):
    ''' Represents an Ethernet device from mypages '''
    pass


class Smartplug(Device):
    ''' Represents a Smartplug device from mypages '''
    STATE_ON = 'on'
    STATE_OFF = 'off'


class Alarm(Device):
    ''' Represents an alarm device from mypages '''
    STATE_ARMED_HOME = 'ARMED_HOME'
    STATE_ARMED_AWAY = 'ARMED_AWAY'
    STATE_DISARMED = 'DISARMED'


class Climate(Device):
    ''' Represents a Climate device from mypages '''
    pass
