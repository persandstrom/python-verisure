"""
A python3 module for reading and changing status of verisure devices through
mypages.
"""
from __future__ import print_function

import requests
import json
import re

DOMAIN = 'https://mypages.verisure.com'
URL_LOGIN = DOMAIN + '/j_spring_security_check?locale=en_GB'
URL_ALARM_STATUS = DOMAIN + '/remotecontrol'
URL_CLIMATE_STATUS = DOMAIN + '/overview/climatedevice'
URL_SMARTPLUG_STATUS = DOMAIN + '/overview/smartplug'
URL_ETHERNET_STATUS = DOMAIN + '/overview/ethernetstatus'
URL_START = DOMAIN + '/uk/start.html'
URL_SMARTPLUG_ONOFF_CMD = DOMAIN + '/smartplugs/onoffplug.cmd'
RESPONSE_TIMEOUT = 3

CSRF_REGEX = re.compile(
    r'\<input type="hidden" name="_csrf" value="' +
    r'(?P<csrf>([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}))' +
    r'" /\>')


class Verisure(object):
    """ Interface to verisure MyPages """

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session = None
        self._csrf = ''

    def __enter__(self):
        """ Enter context manager, open session """
        self._session = requests.Session()
        self.login()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """ Exit context manager, close session """
        self._session.close()
        self._session = None

    def login(self):
        """ Login to mypages """
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

    def _read_status(self, url):
        """ Read all statuses of a device type """
        if not self._session:
            raise ConnectionError('Not logged in')
        response = self._session.get(url)
        return json.loads(response.text)

    def get_alarm_status(self):
        """ Get status from alarm devices """
        return self._read_status(URL_ALARM_STATUS)

    def get_climate_status(self):
        """ Get status from climate devices """
        return self._read_status(URL_CLIMATE_STATUS)

    def get_smartplug_status(self):
        """ Get status of smartplug devices """
        return self._read_status(URL_SMARTPLUG_STATUS)

    def get_ethernet_status(self):
        """ Get status of ethernet devices """
        return self._read_status(URL_ETHERNET_STATUS)

    def set_smartplug_status(self, device_id, value):
        """ set status of a smartplug component (on, off) """
        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        self._set_status(URL_SMARTPLUG_ONOFF_CMD, data)

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

# pylint: disable=C0103
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Read or change status of verisure devices')
    parser.add_argument(
        'username',
        help='MySite username')
    parser.add_argument(
        'password',
        help='MySite password')

    subparsers = parser.add_subparsers(
        help='commands',
        dest='command')

    # Get command
    get_parser = subparsers.add_parser(
        'get',
        help='Read status of one or many device types')
    get_parser.add_argument(
        'devices',
        nargs='+',
        choices=['alarm', 'climate', 'smartplug', 'ethernet'],
        help='Read status for device type',
        default=[])

    # Set command
    set_parser = subparsers.add_parser(
        'set',
        help='Set status of a device')
    set_parser.add_argument(
        'device',
        choices=['smartplug'],
        help='Set status for device type')
    set_parser.add_argument(
        'device_id',
        help='device id')
    set_parser.add_argument(
        'new_value',
        help='new value')

    args = parser.parse_args()

    with Verisure(args.username, args.password) as verisure:
        if args.command == 'get':
            for device in args.devices:
                if device == 'alarm':
                    print(verisure.get_alarm_status())
                if device == 'climate':
                    print(verisure.get_climate_status())
                if device == 'smartplug':
                    print(verisure.get_smartplug_status())
                if device == 'ethernet':
                    print(verisure.get_ethernet_status())
        if args.command == 'set':
            if args.device == 'smartplug':
                verisure.set_smartplug_status(args.device_id, args.new_value)
