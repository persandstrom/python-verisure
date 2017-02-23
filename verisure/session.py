'''
Verisure session, using verisure app api
'''

import base64
import json
import requests

BASE_URL = 'https://e-api01.verisure.com/xbn/2/'

INSTALLATION_URL = BASE_URL + 'installation/{guid}/'
LOGIN_URL = BASE_URL + 'cookie'

GET_INSTALLATIONS_URL = BASE_URL + 'installation/search?email={username}'
OVERVIEW_URL = INSTALLATION_URL + 'overview'
SMARTPLUG_URL = INSTALLATION_URL + 'smartplug/state'
SET_ARMSTATE_URL = INSTALLATION_URL + 'armstate/code'
GET_ARMSTATE_TRANSACTION_URL = \
    INSTALLATION_URL + 'code/result/{transaction_id}'
GET_ARMSTATE_URL = INSTALLATION_URL + 'armstate'
HISTORY_URL = INSTALLATION_URL + 'eventlog'
CLIMATE_URL = INSTALLATION_URL + 'climate/simple/search'
GET_LOCKSTATE_URL = INSTALLATION_URL + 'doorlockstate/search'
SET_LOCKSTATE_URL = INSTALLATION_URL + 'device/{device_label}/{state}'
GET_LOCKSTATE_TRANSACTION_URL = \
    INSTALLATION_URL + 'doorlockstate/change/result/{transaction_id}'
LOCKCONFIG_URL = INSTALLATION_URL + 'device/{device_label}/doorlockconfig'
IMAGECAPTURE_URL = \
    INSTALLATION_URL + 'device/{device_label}/customerimagecamera/imagecapture'
GET_IMAGESERIES_URL = \
    INSTALLATION_URL + 'device/customerimagecamera/imageseries/search'
DOWNLOAD_IMAGE_URL = \
    INSTALLATION_URL + \
    'device/{device_label}/customerimagecamera/image/{image_id}/'
GET_VACATIONMODE_URL = INSTALLATION_URL + 'vacationmode'


def _validate_response(response):
    """ Verify that response is OK """
    if response.status_code == 200:
        return
    raise ResponseError(response.status_code, response.text)


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
                text.encode('utf-8')))
        self.status_code = status_code
        self.text = json.loads(text.encode('utf-8'))


class Session(object):
    """ Verisure app session

    Args:
        username (str): Username used to login to verisure app
        password (str): Password used to login to verisure app

    """

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._vid = None
        self._giid = None
        self.installations = None

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
                headers={
                    'Authorization': auth,
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                })
        except requests.exceptions.RequestException as ex:
            raise LoginError(ex)
        _validate_response(response)
        self._vid = json.loads(response.text)['cookie']
        self._get_installations()
        self._giid = self.installations[0]['giid']

    def _get_installations(self):
        """ Get information about installations """
        response = None
        try:
            response = requests.get(
                GET_INSTALLATIONS_URL.format(username=self._username),
                headers={
                    'Cookie': 'vid={}'.format(self._vid),
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                })
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        self.installations = json.loads(response.text)

    def set_giid(self, giid):
        """ Set installation giid

        Args:
            giid (str): Installation identifier
        """
        self._giid = giid

    def get_overview(self):
        """ Get overview for installation """
        response = None
        try:
            response = requests.get(
                OVERVIEW_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Encoding': 'gzip, deflate',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_smartplug_state(self, device_label, state):
        """ Turn on or off smartplug

        Args:
            device_label (str): Smartplug device label
            state (boolean): new status, 'True' or 'False'
        """
        response = None
        try:
            response = requests.post(
                SMARTPLUG_URL.format(
                    guid=self._giid),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps([{
                    "deviceLabel": device_label,
                    "state": state}]))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)

    def set_arm_state(self, code, state):
        """ Set alarm state

        Args:
            code (str): Personal alarm code (four or six digits)
            state (str): 'ARMED_HOME', 'ARMED_AWAY' or 'DISARMED'
        """
        response = None
        try:
            response = requests.put(
                SET_ARMSTATE_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({"code": str(code), "state": state}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_arm_state_transaction(self, transaction_id=''):
        """ Get arm state transaction status

        Args:
            transaction_id: Transaction ID received from set_arm_state
        """
        response = None
        try:
            response = requests.get(
                GET_ARMSTATE_TRANSACTION_URL.format(
                    guid=self._giid,
                    transaction_id=transaction_id),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_arm_state(self):
        """ Get arm state """
        response = None
        try:
            response = requests.get(
                GET_ARMSTATE_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_history(self, filters=(), pagesize=15, offset=0):
        """ Get recent events

        Args:
            filters (string set): 'ARM', 'DISARM', 'FIRE', 'INTRUSION',
                                  'TECHNICAL', 'SOS', 'WARNING'
            pagesize (int): Number of events to display
            offset (int): Skip pagesize * offset first events
        """
        response = None
        try:
            response = requests.get(
                HISTORY_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)},
                params={
                    "offset": int(offset),
                    "pagesize": int(pagesize),
                    "notificationCategories": filters})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_climate(self, device_label):
        """ Get climate history
        Args:
            device_label: device label of climate device
        """
        response = None
        try:
            response = requests.get(
                CLIMATE_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)},
                params={
                    "deviceLabel": device_label})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_lock_state(self):
        """ Get current lock status """
        response = None
        try:
            response = requests.get(
                GET_LOCKSTATE_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_lock_state(self, code, device_label, state):
        """ Lock or unlock

        Args:
            code (str): Lock code
            device_label (str): device label of lock
            state (str): 'lock' or 'unlock'
        """
        response = None
        try:
            response = requests.put(
                SET_LOCKSTATE_URL.format(
                    guid=self._giid,
                    device_label=device_label,
                    state=state
                ),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({"code": str(code)}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_lock_state_transaction(self, transaction_id=''):
        """ Get lockk state transaction status

        Args:
            transaction_id: Transaction ID received from set_lock_state
        """
        response = None
        try:
            response = requests.get(
                GET_LOCKSTATE_TRANSACTION_URL.format(
                    guid=self._giid,
                    transaction_id=transaction_id),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_lock_config(self, device_label):
        """ Get lock configuration

        Args:
            device_label (str): device label of lock
        """
        response = None
        try:
            response = requests.get(
                LOCKCONFIG_URL.format(
                    guid=self._giid,
                    device_label=device_label
                ),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_lock_config(self, device_label, volume=None, voice_level=None,
                        auto_lock_enabled=None):
        """ Set lock configuration

        Args:
            device_label (str): device label of lock
            volume (str): 'SILENCE', 'LOW' or 'HIGH'
            voice_level (str): 'ESSENTIAL' or 'NORMAL'
            auto_lock_enabled (boolean): auto lock enabled
        """
        response = None
        data = {}
        if volume:
            data['volume'] = volume
        if voice_level:
            data['voiceLevel'] = voice_level
        if auto_lock_enabled is not None:
            data['autoLockEnabled'] = auto_lock_enabled
        try:
            response = requests.put(
                LOCKCONFIG_URL.format(
                    guid=self._giid,
                    device_label=device_label
                ),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps(data))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)

    def capture_image(self, device_label):
        """ Capture smartcam image

        Args:
            device_label (str): device label of camera
        """
        response = None
        try:
            response = requests.post(
                IMAGECAPTURE_URL.format(
                    guid=self._giid,
                    device_label=device_label),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)

    def get_camera_imageseries(self, number_of_imageseries=10, offset=0):
        """ Get smartcam image series

        Args:
            number_of_imageseries (int): number of image series to get
            offset (int): skip offset amount of image series
        """
        response = None
        try:
            response = requests.get(
                GET_IMAGESERIES_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)},
                params={
                    "numberOfImageSeries": int(number_of_imageseries),
                    "offset": int(offset),
                    "fromDate": "",
                    "toDate": "",
                    "onlyNotViewed": "",
                    "_": self._giid})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def download_image(self, device_label, image_id, file_name):
        """ Download image taken by a smartcam

        Args:
            device_label (str): device label of camera
            image_id (str): image id from image series
            file_name (str): path to file
        """
        response = None
        try:
            response = requests.get(
                DOWNLOAD_IMAGE_URL.format(
                    guid=self._giid,
                    device_label=device_label,
                    image_id=image_id),
                headers={
                    'Cookie': 'vid={}'.format(self._vid)},
                stream=True)
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        with open(file_name, 'wb') as image_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    image_file.write(chunk)

    def get_vacation_mode(self):
        """ Get current vacation mode """
        response = None
        try:
            response = requests.get(
                GET_VACATIONMODE_URL.format(
                    guid=self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def logout(self):
        """ Logout and remove vid """
        response = None
        try:
            response = requests.delete(
                LOGIN_URL,
                headers={
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
