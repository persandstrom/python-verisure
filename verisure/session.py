'''
Verisure session, using verisure app api
'''

import base64
import json
import requests
from . import urls
import os


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
                text))
        self.status_code = status_code
        self.text = json.loads(text)


class Session(object):
    """ Verisure app session

    Args:
        username (str): Username used to login to verisure app
        password (str): Password used to login to verisure app

    """

    def __init__(self, username, password,
                 cookieFileName='~/.verisure-cookie'):
        self._username = username
        self._password = password
        self._cookieFileName = os.path.expanduser(cookieFileName)
        self._vid = None
        self._giid = None
        self.installations = None

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
        if os.path.exists(self._cookieFileName):
            with open(self._cookieFileName, 'r') as cookieFile:
                self._vid = cookieFile.read().strip()

            try:
                self._get_installations()
            except ResponseError:
                self._vid = None
                os.remove(self._cookieFileName)

        if self._vid is None:
            self._create_cookie()
            with open(self._cookieFileName, 'w') as cookieFile:
                cookieFile.write(self._vid)
            self._get_installations()

        self._giid = self.installations[0]['giid']

    def _create_cookie(self):
        auth = 'Basic {}'.format(
            base64.b64encode(
                'CPE/{username}:{password}'.format(
                    username=self._username,
                    password=self._password).encode('utf-8')
            ).decode('utf-8'))
        response = None
        for base_url in urls.BASE_URLS:
            urls.BASE_URL = base_url
            try:
                response = requests.post(
                    urls.login(),
                    headers={
                        'Authorization': auth,
                        'Accept': 'application/json,'
                                  'text/javascript, */*; q=0.01',
                    })
                if 2 == response.status_code // 100:
                    break
                elif 503 == response.status_code:
                    continue
                else:
                    raise ResponseError(response.status_code, response.text)
            except requests.exceptions.RequestException as ex:
                raise LoginError(ex)

        _validate_response(response)
        self._vid = json.loads(response.text)['cookie']

    def _get_installations(self):
        """ Get information about installations """
        response = None
        for base_url in urls.BASE_URLS:
            urls.BASE_URL = base_url
            try:
                response = requests.get(
                    urls.get_installations(self._username),
                    headers={
                        'Cookie': 'vid={}'.format(self._vid),
                        'Accept': 'application/json,'
                                  'text/javascript, */*; q=0.01',
                    })
                if 2 == response.status_code // 100:
                    break
                elif 503 == response.status_code:
                    continue
                else:
                    raise ResponseError(response.status_code, response.text)
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
                urls.overview(self._giid),
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
                urls.smartplug(self._giid),
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
                urls.set_armstate(self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({"code": str(code), "state": state}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_arm_state_transaction(self, transaction_id):
        """ Get arm state transaction status

        Args:
            transaction_id: Transaction ID received from set_arm_state
        """
        response = None
        try:
            response = requests.get(
                urls.get_armstate_transaction(self._giid, transaction_id),
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
                urls.get_armstate(self._giid),
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
                                  'TECHNICAL', 'SOS', 'WARNING', 'LOCK',
                                  'UNLOCK'
            pagesize (int): Number of events to display
            offset (int): Skip pagesize * offset first events
        """
        response = None
        try:
            response = requests.get(
                urls.history(self._giid),
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
                urls.climate(self._giid),
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
                urls.get_lockstate(self._giid),
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
                urls.set_lockstate(self._giid, device_label, state),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({"code": str(code)}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_lock_state_transaction(self, transaction_id):
        """ Get lock state transaction status

        Args:
            transaction_id: Transaction ID received from set_lock_state
        """
        response = None
        try:
            response = requests.get(
                urls.get_lockstate_transaction(self._giid, transaction_id),
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
                urls.lockconfig(self._giid, device_label),
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
                urls.lockconfig(self._giid, device_label),
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
                urls.imagecapture(self._giid, device_label),
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
                urls.get_imageseries(self._giid),
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
                urls.download_image(self._giid, device_label, image_id),
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
                urls.get_vacationmode(self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def get_door_window(self):
        """ Get door_window states"""
        response = None
        try:
            response = requests.get(
                urls.door_window(self._giid),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def test_ethernet(self):
        """ Test ethernet status """
        response = None
        try:
            response = requests.post(
                urls.test_ethernet(self._giid),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)

    def logout(self):
        """ Logout and remove vid """
        response = None
        try:
            response = requests.delete(
                urls.login(),
                headers={
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)

    def get_heat_pump_state(self, device_label):
        """ Get heatpump states"""
        response = None
        try:
            response = requests.get(
                urls.get_heatpump_state(self._giid, device_label),
                headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_heat_pump_mode(self, device_label, mode):
        """ Set heatpump mode
        Args:
            mode (str): 'HEAT', 'COOL', 'FAN' or 'AUTO'
        """
        response = None
        try:
            response = requests.put(
                urls.set_heatpump_state(self._giid, device_label),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({'mode': mode}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_heat_pump_power(self, device_label, power):
        """ Set heatpump mode
        Args:
            power (str): 'ON', 'OFF'
        """
        response = None
        try:
            response = requests.put(
                urls.set_heatpump_state(self._giid, device_label),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({'power': power}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_heat_pump_fan_speed(self, device_label, fan_speed):
        """ Set heatpump mode
        Args:
        fan_speed (str): 'LOW', 'MEDIUM_LOW', 'MEDIUM, 'MEDIUM_HIGH' or 'HIGH'
        """
        response = None
        try:
            response = requests.put(
                urls.set_heatpump_state(self._giid, device_label),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({'fanSpeed': fan_speed}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_heat_pump_target_temperature(self, device_label, target_temp):
        """ Set heatpump mode
        Args:
            target_temperature (int): required temperature of the heatpump
        """
        response = None
        try:
            response = requests.put(
                urls.set_heatpump_state(self._giid, device_label),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({'targetTemperature': target_temp}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_heat_pump_feature(self, device_label, feature):
        """ Set heatpump mode
        Args:
            feature: 'QUIET', 'ECONAVI', or 'POWERFUL'
        """
        response = None
        try:
            response = requests.put(
                urls.set_heatpump_feature(self._giid, device_label, feature),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)})
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)

    def set_heat_pump_airswingdirection(self, device_label, airswingdirection):
        """ Set heatpump mode
        Args:
        airSwingDirection (str): 'AUTO' '0_DEGREES' '30_DEGREES'
        '60_DEGREES' '90_DEGREES'
        """
        response = None
        try:
            response = requests.put(
                urls.set_heatpump_state(self._giid, device_label),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cookie': 'vid={}'.format(self._vid)},
                data=json.dumps({'airSwingDirection':
                                {"vertical": airswingdirection}}))
        except requests.exceptions.RequestException as ex:
            raise RequestError(ex)
        _validate_response(response)
        return json.loads(response.text)
