""" Represents a MyPages session """

import json

import re
import shutil


# this import is depending on python version
try:
    import HTMLParser
    UNESCAPE = HTMLParser.HTMLParser().unescape
except ImportError:
    import html
    UNESCAPE = html.unescape

import requests


DOMAIN = 'https://mypages.verisure.com'
URL_LOGIN = DOMAIN + '/j_spring_security_check?locale=en_GB'
URL_START = DOMAIN + '/uk/start.html?inst={inst}'
RESPONSE_TIMEOUT = 10

CSRF_REGEX = re.compile(
    r'\<input type="hidden" name="_csrf" value="' +
    r'(?P<csrf>(.*?))' +
    r'" /\>')

TITLE_REGEX = re.compile(r'\<title\>(?P<title>(.*))\</title\>')


class Error(Exception):
    ''' mypages error '''
    pass


class LoginError(Error):
    ''' login failed '''
    pass


class ResponseError(Error):
    ''' Unexcpected response '''
    pass


class LoggedOutError(ResponseError):
    ''' User logged out '''
    pass


class TemporarilyUnavailableError(ResponseError):
    ''' My Pages is temporarily unavailable '''
    pass


class MaintenanceError(ResponseError):
    ''' My Pages is currently in maintenance '''
    pass


class RequestError(Error):
    ''' Wrapped requests.exceptions.RequestException '''
    pass


class Session(object):
    """ Verisure session """

    def __init__(self, username, password, installation):
        self._session = None
        self._username = username
        self._password = password
        self._installation = installation
        self.csrf = ''

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
            URL_LOGIN,
            cookies=dict(self._session.cookies),
            data=auth
        ).prepare()
        response = None
        try:
            response = self._session.send(req, timeout=RESPONSE_TIMEOUT)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        status = self.json_to_dict(response.text)
        if not status['status'] == 'ok':
            raise LoginError(status['message'])
        self.csrf = self._get_csrf()

    def logout(self):
        """ Ends session

        note:
            Ends the session, will not call the logout command on mypages

        """
        self._session.close()
        self._session = None

    def download(self, url, dest):
        """Download a file from MyPages."""
        self._ensure_session()
        try:
            response = self._session.get(
                DOMAIN + url, stream=True)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        with open((dest), 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)

    def get(self, url, to_json=True, **params):
        """ Read all statuses of a device type """
        self._ensure_session()
        response = None
        try:
            response = self._session.get(
                DOMAIN + url,
                params=params)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        if to_json:
            return self.json_to_dict(UNESCAPE(response.text))
        return response.text

    def post(self, url, data):
        """ send post request """
        self._ensure_session()
        req = requests.Request(
            'POST',
            DOMAIN + url,
            cookies=dict(self._session.cookies),
            headers={'X-CSRF-TOKEN': self.csrf},
            data=data
        ).prepare()
        response = None
        try:
            response = self._session.send(
                req,
                timeout=RESPONSE_TIMEOUT)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        return self.json_to_dict(UNESCAPE(response.text))

    def put(self, url, data):
        """ send put request """
        self._ensure_session()
        req = requests.Request(
            'PUT',
            DOMAIN + url,
            cookies=dict(self._session.cookies),
            headers={
                'X-CSRF-TOKEN': self.csrf,
                'content-type': 'application/json'},
            data=json.dumps(data)
        ).prepare()
        response = None
        try:
            response = self._session.send(
                req,
                timeout=RESPONSE_TIMEOUT)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        return response.text

    def _get_csrf(self):
        """ Retreive X-CSRF-TOKEN from start.html """
        response = None
        try:
            response = self._session.get(
                URL_START.format(inst=self._installation),
                timeout=RESPONSE_TIMEOUT)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        self.validate_response(response)
        match = CSRF_REGEX.search(response.text)
        return match.group('csrf')

    def _ensure_session(self):
        ''' ensures that a session is created '''
        if not self._session:
            raise Error('Session not started')

    def json_to_dict(self, doc):
        ''' transform json with unicode characters to dict '''
        if not doc:
            return ''
        try:
            return json.loads(doc)
        except ValueError as ex:
            self.raise_response_error(
                doc,
                ResponseError(
                    'Unable to convert to JSON, '
                    'Error: {0} - Data: {1}'.format(ex, doc.encode('utf-8'))))

    def validate_response(self, response):
        """ Verify that response is OK """
        if response.status_code == 200:
            return
        self.raise_response_error(
            response.text,
            ResponseError(
                'Unable to validate response form My Pages'
                ', status code: {0} - Data: {1}'.format(
                    response.status_code,
                    response.text.encode('utf-8'))))

    @staticmethod
    def raise_response_error(doc, default_error):
        """ Create correct error type from response """
        match = TITLE_REGEX.search(doc)
        if not match:
            raise default_error
        if match.group('title') == ("My Pages is temporarily unavailable"
                                    "-  Verisure"):
            raise TemporarilyUnavailableError('Temporarily unavailable')
        if match.group('title') == 'My Pages - Maintenance -  Verisure':
            raise MaintenanceError('Maintenance')
        if match.group('title') == 'Choose country - My Pages - Verisure':
            raise LoggedOutError('Not logged in')
        if match.group('title') == 'Log in - My Pages - Verisure':
            raise LoggedOutError('Not logged in')
        raise ResponseError(match)
