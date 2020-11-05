'''
Verisure session, using verisure app api
'''

import json
import requests
import os

from .operations import OPERATIONS

class Error(Exception):
    ''' Verisure session error '''
    pass


class RequestError(Error):
    ''' Wrapped requests.exceptions.RequestException '''
    pass


class LoginError(Error):
    ''' Login failed '''
    pass


class ResponseError(Error):
    ''' Unexcpected response '''
    def __init__(self, status_code, text):
        super(ResponseError, self).__init__(
            'Invalid response'
            ', status code: {0} - Data: {1}'.format(
                status_code,
                text))
        self.status_code = status_code
        self.text = text

class Session(object):
    """ Verisure app session

    Args:
        username (str): Username used to login to verisure app
        password (str): Password used to login to verisure app
        cookieFileName (str): path to cookie file

    """

    def __init__(self, username, password,
                 cookieFileName='~/.verisure-cookie'):
        self._username = username
        self._password = password
        self._cookieFileName = os.path.expanduser(cookieFileName)
        self._vid = None
        self._giid = None
        self._base_url = None

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
        """ If of interest, add exception handler
        """

    def login(self):
        """ Login to verisure app api

        Login before calling any read or write commands

        """
        for url in ['https://m-api01.verisure.com', 'https://m-api02.verisure.com']:
            self._base_url = url
            try:
                response = requests.post(
                    '{base_url}/auth/login'.format(base_url=self._base_url),
                    headers={'Accept': 'application/json;charset=UTF-8', 'Content-Type': 'application/xml;charset=UTF-8'},
                    auth=(self._username, self._password))
                if 2 == response.status_code // 100:
                    break
                elif 503 == response.status_code:
                    continue
                else:
                    raise ResponseError(response.status_code, response.text)
            except requests.exceptions.RequestException as ex:
                raise LoginError(ex)

        self._cookies = response.cookies
        return self.get_installations()

        
        #self._vid = json.loads(response.text)['cookie']
        #exit()
       #     with open(self._cookieFileName, 'r') as cookieFile:
       #         self._vid = cookieFile.read().strip()
        #
        #    try:
        #        self._get_installations()
        #    except ResponseError:
        #        self._vid = None
        #        os.remove(self._cookieFileName)

        #if self._vid is None:
        #    self._create_cookie()
        #    with open(self._cookieFileName, 'w') as cookieFile:
        #        cookieFile.write(self._vid)
        #    self._get_installations()

     #   self._giid = self.installations[0]['giid']

    #def _create_cookie(self):

    def query(self, operation, **variables):
        for key, value in operation["session_variables"].items():
            if key == "email":
                variables[key] = self._username
            elif key == "giid":
                variables[key] = self._giid
            elif value:
                variables[key] = value
        return {
            "operationName": operation["name"],
            "variables": variables,
            "query": operation["query"]
        }

    def request(self, *operations):
        print(json.dumps(list(operations)))
        response = requests.post(
            '{base_url}/graphql'.format(base_url=self._base_url),
            headers={'accept': '*.*', 'APPLICATION_ID': 'MyMobile_via_GraphQL' },
            cookies=self._cookies,
            data=json.dumps(list(operations))
        )
        if response.status_code != 200:
            raise ResponseError(response.status_code, response.text)
        return json.loads(response.text)

    def get_installations(self):
        """ Get information about installations """
        return self.request(
            self.query(
                OPERATIONS["fetch_all_installations"], email=self._username))

    def set_giid(self, giid):
        """ Set installation giid

        Args:
            giid (str): Installation identifier
        """
        self._giid = giid