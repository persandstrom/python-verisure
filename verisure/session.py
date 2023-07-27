'''
Verisure session, using verisure app api
'''

import json
import os
import pickle

import requests


class Error(Exception):
    ''' Verisure session error '''


class RequestError(Error):
    ''' Request '''


class LoginError(Error):
    ''' Login failed '''


class LogoutError(Error):
    ''' Logout failed '''


class ResponseError(Error):
    ''' Unexcpected response '''
    def __init__(self, status_code, text):
        super().__init__(
            f'Invalid response, status code: {status_code} - Data: {text}')


def query_func(f):
    """A wrapper that indicates that the function is a query (used by CLI)"""
    f.is_query = True
    return f


class VariableTypes:
    """Types for query parameters"""
    class DeviceLabel(str):
        """Device label"""

    class TransactionId(str):
        """Transaction ID"""

    class RequestId(str):
        """Request ID"""

    class ArmFutureState(str):
        """Arm state"""
        # ARMED_AWAY, DISARMED, ARMED_HOME

    class LockFutureState(str):
        """Lock state"""

    class Code(str):
        """Code"""

    class Giid(str):
        """Giid"""


class Session(object):
    """ Verisure app session

    Args:
        username (str): Username used to login to verisure app
        password (str): Password used to login to verisure app
        cookie_file_name (str): path to cookie file

    """

    def __init__(self, username, password,
                 cookie_file_name='~/.verisure-cookie'):
        self._username = username
        self._password = password
        self._cookies = None
        self._cookie_file_name = os.path.expanduser(cookie_file_name)
        self._giid = None
        self._base_url = None
        self._stepup = None
        self._base_urls = ['https://automation01.verisure.com',
                           'https://automation02.verisure.com']
        self._post = self._wrap_request(requests.post)
        self._delete = self._wrap_request(requests.delete)
        self._get = self._wrap_request(requests.get)


    def _wrap_request(self, function):
        """
        Used to wrap methods from the requests module to try both urls and remember
        the last working one.
        """

        def wrapper(url, *args, **kwargs):
            last_exception = Error("Unknown error")
            base_urls = self._base_urls.copy()
            for base_url in base_urls:
                try:
                    response = function(base_url+url, *args, **kwargs)
                    if response.status_code >= 500:
                        last_exception = ResponseError(response.status_code, response.text)
                        self._base_urls.reverse()
                        continue
                    if response.status_code >= 400:
                        last_exception = LoginError(response.text)
                        break
                    if response.status_code == 200:
                        return response
                except requests.exceptions.RequestException as ex:
                    last_exception = RequestError(str(ex))
                self._base_urls.reverse()
            raise last_exception
        return wrapper


    def login(self):
        """ Login to verisure app api
        Login before calling any read or write commands
        Return installations
        """

        response = self._post(
            "/auth/login",
            headers={'APPLICATION_ID': 'PS_PYTHON'},
            auth=(self._username, self._password))

        if "stepUpToken" in response.text:
            raise LoginError("Multifactor authentication enabled, "
                             "disable or create MFA cookie")

        self._cookies = response.cookies
        with open(self._cookie_file_name, 'wb') as f:
            pickle.dump(self._cookies, f)

        installations = self.get_installations()
        if 'errors' not in installations:
            return installations

        raise LoginError("Failed to log in")

    def request_mfa(self):
        """ Request MFA verification code """

        response = self._post(
            url="/auth/login",
            headers={'APPLICATION_ID': 'PS_PYTHON'},
            auth=(self._username, self._password))

        if "stepUpToken" not in response.text:
            raise LoginError("Multifactor authentication disabled, "
                             "use regular login instead")

        self._cookies = response.cookies
        for mfa_type in ['phone', 'email']:
            try:
                mfa_response = self._post(
                    url=f"/auth/mfa?type={mfa_type}",
                    headers={'APPLICATION_ID': 'PS_PYTHON'},
                    cookies=self._cookies)
                if mfa_response.status_code == 200:
                    return
            except Exception as ex:
                raise LoginError("Failed to request MFA type") from ex

        raise LoginError("Failed to log in")

    def validate_mfa(self, code):
        """ Validate mfa request
        Return installations
        """

        response = self._post(
            url="/auth/mfa/validate",
            headers={
                'APPLICATION_ID': 'PS_PYTHON',
                'Accept': 'application/json',
                'Content-Type': 'application/json'},
            cookies=self._cookies,
            data=json.dumps({"token": code}))

        self._cookies = response.cookies
        with open(self._cookie_file_name, 'wb') as cookie_file:
            pickle.dump(self._cookies, cookie_file)

        installations = self.get_installations()
        if 'errors' not in installations:
            return installations

        raise LoginError("Failed to log in")

    def login_cookie(self):
        """ Login using cookie
        Return installations
        """

        # Load cookie from file
        try:
            with open(self._cookie_file_name, 'rb') as cookie_file:
                self._cookies = pickle.load(cookie_file)
        except Exception as ex:
            raise LoginError("Failed to read cookie") from ex

        # Update cookie
        self.update_cookie()

        installations = self.get_installations()
        if 'errors' not in installations:
            return installations

        raise LoginError("Failed to log in")

    def update_cookie(self):
        """ Update expired cookie
        Cookie can last 15 minutes before it needs to be updated.
        """

        response = self._get(
            url="/auth/token",
            headers={'APPLICATION_ID': 'PS_PYTHON'},
            cookies=self._cookies)

        self._cookies.update(response.cookies)
        with open(self._cookie_file_name, 'wb') as cookie_file:
            pickle.dump(self._cookies, cookie_file)

    def logout(self):
        """ Log out from the verisure app api """
        try:
            self._delete(
                url="/auth/logout",
                headers={'APPLICATION_ID': 'PS_PYTHON'},
                cookies=self._cookies)
        finally:
            self._base_url = None
            self._giid = None
            self._cookies = None
            self._stepup = None
            if os.path.exists(self._cookie_file_name):
                os.remove(self._cookie_file_name)

    def request(self, *operations):
        """Request operations"""
        response = self._post(
            '/graphql',
            headers={
                'APPLICATION_ID': 'PS_PYTHON',
                'Accept': 'application/json'},
            cookies=self._cookies,
            data=json.dumps(list(operations)))
        return json.loads(response.text)

    def get_installations(self):
        """ Get information about installations """
        return self.request(self.fetch_all_installations())

    def set_giid(self, giid):
        """ Set installation giid

        Args:
            giid (str): Installation identifier
        """
        self._giid = giid

    @query_func
    def arm_away(self,
                 code: VariableTypes.Code,
                 giid: VariableTypes.Giid=None):
        """Set arm status away"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "armAway",
            "variables": {
                "giid": giid or self._giid,
                "code": code},
            "query": "mutation armAway($giid: String!, $code: String!) {\n  armStateArmAway(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def arm_home(self,
                 code: VariableTypes.Code,
                 giid: VariableTypes.Giid=None):
        """Set arm state home"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "armHome",
            "variables": {
                "giid": giid or self._giid,
                "code": code},
            "query": "mutation armHome($giid: String!, $code: String!) {\n  armStateArmHome(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def arm_state(self,
                  giid: VariableTypes.Giid=None):
        """Read arm state"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "ArmState",
            "variables": {
                "giid": giid or self._giid},
            "query": "query ArmState($giid: String!) {\n  installation(giid: $giid) {\n    armState {\n      type\n      statusType\n      date\n      name\n      changedVia\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def broadband(self,
                  giid: VariableTypes.Giid=None):
        """Get broadband status"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "Broadband",
            "variables": {
                "giid": giid or self._giid},
            "query": "query Broadband($giid: String!) {\n  installation(giid: $giid) {\n    broadband {\n      testDate\n      isBroadbandConnected\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def capability(self,
                   giid: VariableTypes.Giid=None):
        """Get capability"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "Capability",
            "variables": {
                "giid": giid or self._giid},
            "query": "query Capability($giid: String!) {\n  installation(giid: $giid) {\n    capability {\n      current\n      gained {\n        capability\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def charge_sms(self,
                   giid: VariableTypes.Giid=None):
        """Charge SMS"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "ChargeSms",
            "variables": {
                "giid": giid or self._giid},
            "query": "query ChargeSms($giid: String!) {\n  installation(giid: $giid) {\n    chargeSms {\n      chargeSmartPlugOnOff\n      chargeLockUnlock\n      chargeArmDisarm\n      chargeNotifications\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def climate(self,
                giid: VariableTypes.Giid=None):
        """Get climate"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "Climate",
            "variables": {
                "giid": giid or self._giid},
            "query": "query Climate($giid: String!) {\n  installation(giid: $giid) {\n    climates {\n      device {\n        deviceLabel\n        area\n        gui {\n          label\n          __typename\n        }\n        __typename\n      }\n      humidityEnabled\n      humidityTimestamp\n      humidityValue\n      temperatureTimestamp\n      temperatureValue\n      thresholds {\n        aboveMaxAlert\n        belowMinAlert\n        sensorType\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def disarm(self,
               code: VariableTypes.Code,
               giid: VariableTypes.Giid=None):
        """Disarm alarm"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "disarm",
            "variables": {
                "giid": giid or self._giid,
                "code": code},
            "query": "mutation disarm($giid: String!, $code: String!) {\n  armStateDisarm(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def door_lock(self,
                  device_label: VariableTypes.DeviceLabel,
                  code: VariableTypes.Code,
                  giid: VariableTypes.Giid=None):
        """Lock door"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "DoorLock",
            "variables": {
                "giid": giid or self._giid,
                "deviceLabel": device_label,
                "input": {
                    "code": code,
                },
            },
            "query": "mutation DoorLock($giid: String!, $deviceLabel: String!, $input: LockDoorInput!) {\n  DoorLock(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_lock_configuration(self,
                                device_label: VariableTypes.DeviceLabel,
                                giid: VariableTypes.Giid=None):
        """Get door lock configuration"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "DoorLockConfiguration",
            "variables": {
                "giid": giid or self._giid,
                "deviceLabel": device_label},
            "query": "query DoorLockConfiguration($giid: String!, $deviceLabel: String!) {\n  installation(giid: $giid) {\n    smartLocks(filter: {deviceLabels: [$deviceLabel]}) {\n      device {\n        area\n        deviceLabel\n        __typename\n      }\n      configuration {\n        ... on YaleLockConfiguration {\n          autoLockEnabled\n          voiceLevel\n          volume\n          __typename\n        }\n        ... on DanaLockConfiguration {\n          holdBackLatchDuration\n          twistAssistEnabled\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def set_autolock_enabled(self,
                             device_label: VariableTypes.DeviceLabel,
                             auto_lock_enabled: bool,
                             giid: VariableTypes.Giid=None):
        """Enable or disable autolock"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "DoorLockUpdateConfig",
            "variables": {
                "giid": giid or self._giid,
                "deviceLabel": device_label,
                "input": {
                    "autoLockEnabled": auto_lock_enabled
                }
            },
            "query": "mutation DoorLockUpdateConfig($giid: String!, $deviceLabel: String!, $input: DoorLockUpdateConfigInput!) {\n  DoorLockUpdateConfig(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_unlock(self,
                    device_label: VariableTypes.DeviceLabel,
                    code: VariableTypes.Code,
                    giid: VariableTypes.Giid=None):
        """Unlock door"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "DoorUnlock",
            "variables": {
                "giid": giid or self._giid,
                "deviceLabel": device_label,
                "input": {
                    "code": code,
                },
            },
            "query": "mutation DoorUnlock($giid: String!, $deviceLabel: String!, $input: LockDoorInput!) {\n  DoorUnlock(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_window(self,
                    giid: VariableTypes.Giid=None):
        """Read status of door and window sensors"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "DoorWindow",
            "variables": {
                "giid": giid or self._giid},
            "query": "query DoorWindow($giid: String!) {\n  installation(giid: $giid) {\n    doorWindows {\n      device {\n        deviceLabel\n        __typename\n      }\n      type\n      area\n      state\n      wired\n      reportTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def event_log(self,
                  giid: VariableTypes.Giid=None):
        """Read event log"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "EventLog",
            "variables": {
                "giid": giid or self._giid,
                "offset": 0,
                "pagesize": 15,
                "eventCategories": ["INTRUSION", "FIRE", "SOS", "WATER", "ANIMAL", "TECHNICAL", "WARNING", "ARM", "DISARM", "LOCK", "UNLOCK", "PICTURE", "CLIMATE", "CAMERA_SETTINGS"],  # noqa: E501
                "eventContactIds": [],
                "eventDeviceLabels": [],
                "fromDate": None,
                "toDate": None
            },
            "query": "query EventLog($giid: String!, $offset: Int!, $pagesize: Int!, $eventCategories: [String], $fromDate: String, $toDate: String, $eventContactIds: [String], $eventDeviceLabels: [String]) {\n  installation(giid: $giid) {\n    eventLog(offset: $offset, pagesize: $pagesize, eventCategories: $eventCategories, eventContactIds: $eventContactIds, eventDeviceLabels: $eventDeviceLabels, fromDate: $fromDate, toDate: $toDate) {\n      moreDataAvailable\n      pagedList {\n        device {\n          deviceLabel\n          area\n          gui {\n            label\n            __typename\n          }\n          __typename\n        }\n        arloDevice {\n          name\n          __typename\n        }\n        gatewayArea\n        eventType\n        eventCategory\n        eventSource\n        eventId\n        eventTime\n        userName\n        armState\n        userType\n        climateValue\n        sensorType\n        eventCount\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def fetch_all_installations(self):
        """Fetch installations"""
        return {
            "operationName": "fetchAllInstallations",
            "variables": {
                "email": self._username},
            "query": "query fetchAllInstallations($email: String!){\n  account(email: $email) {\n    installations {\n      giid\n      alias\n      customerType\n      dealerId\n      subsidiary\n      pinCodeLength\n      locale\n      address {\n        street\n        city\n        postalNumber\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }
    
    @query_func
    def firmware(self,
                 giid: VariableTypes.Giid=None):
        """Get firmware information"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
	        "operationName": "Firmware",
	        "variables": {
		        "giid": giid or self._giid
	        },
	        "query": "query Firmware($giid: String!) {\n  installation(giid: $giid) {\n    firmware {\n      status {\n        latestFirmware\n        requestedFirmware\n        upgradeable\n        status\n        gateways {\n          reportedRunningFirmware\n          deviceLabel\n          status\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n" # noqa: E501
        }

    @query_func
    def guardian_sos(self):
        """Guardian SOS"""
        return {
            "operationName": "GuardianSos",
            "variables": {},
            "query": "query GuardianSos {\n  guardianSos {\n    serverTime\n    sos {\n      fullName\n      phone\n      deviceId\n      deviceName\n      giid\n      type\n      username\n      expireDate\n      warnBeforeExpireDate\n      contactId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def is_guardian_activated(self,
                              giid: VariableTypes.Giid=None):
        """Is guardian activated"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "IsGuardianActivated",
            "variables": {
                "giid": giid or self._giid,
                "featureName": "GUARDIAN"},
            "query": "query IsGuardianActivated($giid: String!, $featureName: String!) {\n  installation(giid: $giid) {\n    activatedFeature {\n      isFeatureActivated(featureName: $featureName)\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def permissions(self,
                    giid: VariableTypes.Giid=None):
        """Permissions"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "Permissions",
            "variables": {
                "giid": giid or self._giid,
                "email": self._username},
            "query": "query Permissions($giid: String!, $email: String!) {\n  permissions(giid: $giid, email: $email) {\n    accountPermissionsHash\n    name\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def poll_arm_state(self,
                       transaction_id: VariableTypes.TransactionId,
                       future_state: VariableTypes.ArmFutureState,
                       giid: VariableTypes.Giid=None):
        """Poll arm state"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "pollArmState",
            "variables": {
                "giid": giid or self._giid,
                "transactionId": transaction_id,
                "futureState": future_state},
            "query": "query pollArmState($giid: String!, $transactionId: String, $futureState: ArmStateStatusTypes!) {\n  installation(giid: $giid) {\n    armStateChangePollResult(transactionId: $transactionId, futureState: $futureState) {\n      result\n      createTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def poll_lock_state(self,
                        transaction_id: VariableTypes.TransactionId,
                        device_label: VariableTypes.DeviceLabel,
                        future_state: VariableTypes.LockFutureState,
                        giid: VariableTypes.Giid=None):
        """Poll lock state"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "pollLockState",
            "variables": {
                "giid": giid or self._giid,
                "transactionId": transaction_id,
                "deviceLabel": device_label,
                "futureState": future_state},
            "query": "query pollLockState($giid: String!, $transactionId: String, $deviceLabel: String!, $futureState: DoorLockState!) {\n  installation(giid: $giid) {\n    doorLockStateChangePollResult(transactionId: $transactionId, deviceLabel: $deviceLabel, futureState: $futureState) {\n      result\n      createTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def remaining_sms(self,
                      giid: VariableTypes.Giid=None):
        """Get remaing number of SMS"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "RemainingSms",
            "variables": {
                "giid": giid or self._giid},
            "query": "query RemainingSms($giid: String!) {\n  installation(giid: $giid) {\n    remainingSms\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def smart_button(self,
                     giid: VariableTypes.Giid=None):
        """Get smart button state"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "SmartButton",
            "variables": {
                "giid": giid or self._giid},
            "query": "query SmartButton($giid: String!) {\n  installation(giid: $giid) {\n    smartButton {\n      entries {\n        smartButtonId\n        icon\n        label\n        color\n        active\n        action {\n          actionType\n          expectedState\n          target {\n            ... on Installation {\n              alias\n              __typename\n            }\n            ... on Device {\n              deviceLabel\n              area\n              gui {\n                label\n                __typename\n              }\n              featureStatuses(type: \"SmartPlug\") {\n                device {\n                  deviceLabel\n                  __typename\n                }\n                ... on SmartPlug {\n                  icon\n                  isHazardous\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def smart_lock(self,
                   giid: VariableTypes.Giid=None):
        """Get smart lock state"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "SmartLock",
            "variables": {
                "giid": giid or self._giid},
            "query": "query SmartLock($giid: String!) {\n  installation(giid: $giid) {\n    smartLocks {\n      lockStatus\n      doorState\n      lockMethod\n      eventTime\n      doorLockType\n      secureMode\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      user {\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def set_smartplug(self,
                      device_label: VariableTypes.DeviceLabel,
                      state: bool,
                      giid: VariableTypes.Giid=None):
        """Set state of smart plug"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "UpdateState",
            "variables": {
                "giid": giid or self._giid,
                "deviceLabel": device_label,
                "state": state},
            "query": "mutation UpdateState($giid: String!, $deviceLabel: String!, $state: Boolean!) {\n  SmartPlugSetState(giid: $giid, input: [{deviceLabel: $deviceLabel, state: $state}])}",  # noqa: E501
        }

    @query_func
    def smartplug(self,
                  device_label: VariableTypes.DeviceLabel,
                  giid: VariableTypes.Giid=None):
        """Read status of a single smart plug"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "SmartPlug",
            "variables": {
                "giid": giid or self._giid,
                "deviceLabel": device_label},
            "query": "query SmartPlug($giid: String!, $deviceLabel: String!) {\n  installation(giid: $giid) {\n    smartplugs(filter: {deviceLabels: [$deviceLabel]}) {\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      currentState\n      icon\n      isHazardous\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def smartplugs(self,
                   giid: VariableTypes.Giid=None):
        """Read status of all smart plugs"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "SmartPlug",
            "variables": {
                "giid": giid or self._giid},
            "query": "query SmartPlug($giid: String!) {\n  installation(giid: $giid) {\n    smartplugs {\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      currentState\n      icon\n      isHazardous\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def user_trackings(self,
                       giid: VariableTypes.Giid=None):
        """Read user tracking status"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "userTrackings",
            "variables": {
                "giid": giid or self._giid},
            "query": "query userTrackings($giid: String!) {\n  installation(giid: $giid) {\n    userTrackings {\n      isCallingUser\n      webAccount\n      status\n      xbnContactId\n      currentLocationName\n      deviceId\n      name\n      initials\n      currentLocationTimestamp\n      deviceName\n      currentLocationId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def cameras(self,
                giid: VariableTypes.Giid=None):
        """Get cameras state"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "Camera",
            "variables": {
                "all": True,
                "giid": giid or self._giid},
            "query": "query Camera($giid: String!, $all: Boolean!) {\n    installation(giid: $giid) {\n        cameras(allCameras: $all) {\n            visibleOnCard\n            initiallyConfigured\n            imageCaptureAllowed\n            imageCaptureAllowedByArmstate\n            device {\n        deviceLabel\n        area\n        __typename\n      }\n            latestCameraSeries {\n                image {\n                    imageId\n                    imageStatus\n                    captureTime\n                    url\n                }\n            }\n        }\n    }\n}",  # noqa: E501
            }

    @query_func
    def cameras_last_image(self,
                           giid: VariableTypes.Giid=None):
        """Get cameras last image"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "variables": {
                "giid": giid or self._giid},
            "query": "query queryCaptureImageRequestStatus($giid: String!) {\n  installation(giid: $giid) {\n    cameraContentProvider {\n      latestImage {\n        deviceLabel\n        mediaId\n        contentType\n        contentUrl\n        timestamp\n        duration\n        thumbnailUrl\n        bitRate\n        width\n        height\n        codec\n      }\n    }\n  }\n}",  # noqa: E501
            }

    @query_func
    def cameras_image_series(self, 
                             limit=50,
                             offset=0,
                             giid: VariableTypes.Giid=None):
        """Get the cameras image series"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "operationName": "GQL_CCCP_SearchMedia",
            "variables": {
                "giid": giid or self._giid,
                "limit": limit,
                "offset": offset},
            "query": "mutation GQL_CCCP_SearchMedia(\n	$giid: BigInt!\n	$offset: Int\n	$limit: Int\n	$fromDate: Date\n	$toDate: Date) {\n\n	ContentProviderMediaSearch(\n		giid: $giid\n		offset: $offset\n		limit: $limit\n		fromDate: $fromDate\n		toDate: $toDate\n	) {\n		totalNumberOfMediaSeries\n		mediaSeriesList {\n			seriesId\n			storageType\n			viewed\n			timestamp\n			deviceMediaList {\n				contentUrl\n				mediaAvailable\n				deviceLabel\n				mediaId\n				contentType\n				timestamp\n				requestTimestamp\n				duration\n				expiryDate\n				viewed\n				thumbnailUrl\n				bitRate\n				width\n				height\n				codec\n			}\n		}\n	}\n}",  # noqa: E501}
        }

    @query_func
    def camera_get_request_id(self,
                             device_label: VariableTypes.DeviceLabel,
                             giid: VariableTypes.Giid=None):
        """Get requestId for camera_capture"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "variables": {
                "deviceIdentifier": "RandomString",
                "deviceLabel": device_label,
                "giid": giid or self._giid,
                "resolution": "high"},
            "query": "mutation cccp($giid: String!, $deviceLabel: String!, $resolution: String!, $deviceIdentifier: String) {\n  ContentProviderCaptureImageRequest(giid: $giid, deviceLabel: $deviceLabel, resolution: $resolution, deviceIdentifier: $deviceIdentifier) {\n    requestId\n  }\n}",  # noqa: E501
            }

    @query_func
    def camera_capture(self,
                       device_label: VariableTypes.DeviceLabel,
                       request_id: VariableTypes.RequestId,
                       giid: VariableTypes.Giid=None):
        """Capture a new image from a camera"""
        assert giid or self._giid, "Set default giid or pass explicit"
        return {
            "variables": {
                "deviceLabel": device_label,
                "giid": giid or self._giid,
                "requestId": request_id},
            "query": "query queryCaptureImageRequestStatus($giid: String!, $deviceLabel: String!, $requestId: BigInt!) {\n  installation(giid: $giid) {\n    cameraContentProvider {\n      captureImageRequestStatus(deviceLabel: $deviceLabel, requestId: $requestId) {\n        mediaRequestStatus\n      }\n    }\n  }\n}",  # noqa: E501
            }

    def download_image(self, image_url, file_name):
        """Download image from url"""
        try:
            response = requests.get(image_url, stream=True)
        except requests.exceptions.RequestException as ex:
            raise RequestError("Failed to get image") from ex
        with open(file_name, 'wb') as image_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    image_file.write(chunk)
