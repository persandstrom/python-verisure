""" Represents a MyPages session """

import re
import requests

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
RESPONSE_TIMEOUT = 3
CSRF_REGEX = re.compile(
    r'\<input type="hidden" name="_csrf" value="' +
    r'(?P<csrf>([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}))' +
    r'" /\>')

class Error(Exception):
    ''' mypages error '''
    pass


class LoginError(Error):
    ''' login failed '''
    pass


class ResponseError(Error):
    ''' Unexcpected response '''
    pass


class Session(object):
    """ Verisure session """
    def __init__(self, username, password):
        self._session = None
        self._username = username
        self._password = password
        self._csrf = ''

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
        response = self._session.send(req, timeout=RESPONSE_TIMEOUT)
        self.validate_response(response)
        status = None
        try:
            status = self.json_to_dict(response.text)
        except:
            raise LoginError('Login failed, myPages might be down')
        if not status['status'] == 'ok':
            raise LoginError(status['message'])

    def logout(self):
        """ Ends session

        note:
            Ends the session, will not call the logout command on mypages

        """
        self._session.close()
        self._session = None

    def get(self, url):
        """ Read all statuses of a device type """

        self._ensure_session()
        response = self._session.get(DOMAIN + url)
        return self.json_to_dict(response.text)

    def post(self, url, data):
        """ set status of a component """

        self._ensure_session()
        req = requests.Request(
            'POST',
            DOMAIN + url,
            cookies=dict(self._session.cookies),
            headers={'X-CSRF-TOKEN': self._get_csrf()}, #  WHY DO THIS EVERY TIME??
            data=data
            ).prepare()
        response = self._session.send(
            req,
            timeout=RESPONSE_TIMEOUT)
        self.validate_response(response)
        return response.text

    def _get_csrf(self):
        """ Retreive X-CSRF-TOKEN from start.html """

        response = self._session.get(
            URL_START,
            timeout=RESPONSE_TIMEOUT)
        self.validate_response(response)
        match = CSRF_REGEX.search(response.text)
        return match.group('csrf')

    def _ensure_session(self):
        ''' ensures that a session is created '''

        if not self._session:
            raise Error('Session not started')

    # pylint: disable=W0612,W0123
    @staticmethod
    def json_to_dict(json):
        ''' transform json with unicode characters to dict '''

        true, false, null = True, False, None
        return eval(UNESCAPE(json))

    @staticmethod
    def validate_response(response):
        """ Verify that response is OK """

        if response.status_code != 200:
            raise ResponseError(
                'status code: {} - {}'.format(
                    response.status_code,
                    response.text))

