import base64
import json
import requests
import pprint
from .xmldeserializer import deserialize


BASE_URL = 'https://e-api02.verisure.com/xbn/2/'
LOGIN_URL = BASE_URL + 'cookie'
INSTALLATION_URL = BASE_URL + 'installation/search?email={username}'
OVERVIEW_URL = BASE_URL + 'installation/{guid}/overview'
SMARTPLUG_URL = BASE_URL + 'installation/{guid}/smartplug/state'
RESPONSE_TIMEOUT = 10

class Error(Exception):
    ''' Verisure session error '''
    pass

class RequestError(Error):
    ''' Wrapped requests.exceptions.RequestException '''
    pass

class LoginError(Error):
    ''' Login failed '''
    pass

class LoggedOutError(Error):
    ''' Login failed '''
    pass

class MaintenanceError(Error):
    ''' Login failed '''
    pass

class TemporarilyUnavailableError(Error):
    ''' Login failed '''
    pass

class ResponseError(Error):
    ''' Unexcpected response '''
    pass

class Session(object):
    """ Verisure app session """

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._vid = None


    def login(self):
        """ Login to verisure app api

        Login before calling any read or write commands

        """
        auth = 'Basic {}'.format(
                base64.b64encode(
                    'CPE/{username}:{password}'.format(
                    username=self._username,
                    password=self._password).encode('ascii')
                    ).decode('utf-8'))
        response = None
        try:
            response = requests.post(
                LOGIN_URL,
                headers={'Authorization': auth})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        self._vid = deserialize(response.text)[0].cookie
        self.get_installations()
    
    def validate_response(self, response):
        """ Verify that response is OK """
        if response.status_code == 200:
            return
        raise ResponseError(
            'Unable to validate response form My Pages'
            ', status code: {0} - Data: {1}'.format(
                response.status_code,
                response.text.encode('utf-8')))

    def get_installations(self):
        """ Get information about installations """
        response=None
        try:
            response = requests.get(
                INSTALLATION_URL.format(username=self._username),
                headers={'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        self._installations = deserialize(response.text)
        return self._installations

    def get_overview(self):
        """ Get overview for installation """
        response=None
        try:
            response = requests.get(
                OVERVIEW_URL.format(
                    guid=self._installations[0].giid),
                headers={'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        return deserialize(response.text)[0]

    def set_smartplug_state(self, device_label, state):
        response=None
        try:
            response = requests.post(
                SMARTPLUG_URL.format(
                    guid=self._installations[0].giid),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps([{"deviceLabel": device_label, "state": state}]))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)

    def logout(self):
        pass

