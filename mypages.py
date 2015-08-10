"""
API to communicate with mypages
"""

import requests
import re
import HTMLParser

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

DEVICE_ALARM = 'alarm'
DEVICE_SMARTPLUG = 'smartplug'
DEVICE_ETHERNET = 'ethernet'
DEVICE_CLIMATE = 'climate'

SMARTPLUG_ON = 'on'
SMARTPLUG_OFF = 'off'

ALARM_STATUS_ARMED_HOME = 'ARMED_HOME'
ALARM_STATUS_ARMED_AWAY = 'ARMED_AWAY'
ALARM_STATUS_DISARMED = 'DISARMED'


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
        self.unescape = HTMLParser.HTMLParser().unescape

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
        if response.status_code != 200:
            raise ConnectionError(
                'status code: {} - {}'.format(
                    response.status_code,
                    response.text))

    def logout(self):
        """ Ends session """
        self._session.close()
        self._session = None

    def _read_status(self, device_type, url):
        """ Read all statuses of a device type """
        if not self._session:
            raise ConnectionError('Not logged in')
        response = self._session.get(url)
        status_array = None
        exec(
            "true, false = True, False\n" +
            "status_array = " + self.unescape(response.text))
        return [DeviceStatus(device_type, status) for status in status_array]

    def get_alarm_status(self):
        """ Get status from alarm devices """
        return self._read_status(DEVICE_ALARM, URL_ALARM_STATUS)

    def get_climate_status(self):
        """ Get status from climate devices """
        return self._read_status(DEVICE_CLIMATE, URL_CLIMATE_STATUS)

    def get_smartplug_status(self):
        """ Get status of smartplug devices """
        return self._read_status(DEVICE_SMARTPLUG, URL_SMARTPLUG_STATUS)

    def get_ethernet_status(self):
        """ Get status of ethernet devices """
        return self._read_status(DEVICE_ETHERNET, URL_ETHERNET_STATUS)

    def set_smartplug_status(self, device_id, value):
        """ set status of a smartplug component (on, off) """
        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        self._set_status(URL_SMARTPLUG_ONOFF_CMD, data)

    def set_alarm_status(self, code, state):
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
        if response.status_code != 200:
            raise ConnectionError(
                'status code: {} - {}'.format(
                    response.status_code,
                    response.text))
        return response.text

    def _get_csrf(self):
        """ Retreive X-CSRF-TOKEN from start.html """
        response = self._session.get(URL_START, timeout=RESPONSE_TIMEOUT)
        if response.status_code != 200:
            raise ConnectionError(
                'status code: {} - {}'.format(
                    response.status_code,
                    response.text))
        match = CSRF_REGEX.search(response.text)
        return match.group('csrf')


class DeviceStatus(object):
    def __init__(self, device_type, status):
        self.device_type = device_type
        self.__dict__.update(status)
