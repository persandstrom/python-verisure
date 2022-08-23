'''
Verisure session, using verisure app api
'''

import json
import os
import pickle
import requests


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


def query_func(f):
    f.is_query = True
    return f


class VariableTypes:
    class DeviceLabel(str):
        pass

    class TransactionId(str):
        pass

    class RequestId(str):
        pass

    class ArmFutureState(str):
        # ARMED_AWAY, DISARMED, ARMED_HOME
        pass

    class LockFutureState(str):
        pass

    class Code(str):
        pass


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
        self._cookies = None
        self._cookieFileName = os.path.expanduser(cookieFileName)
        self._giid = None
        self._base_url = None

    def __enter__(self):
        self.login()
        return self

    def login(self):
        """ Login to verisure app api

        Login before calling any read or write commands

        """

        # Read the cookie
        try:
            with open(self._cookieFileName, 'rb') as f:
                self._cookies = pickle.load(f)
        except Exception:
            # Maybe an stderr print would be good?
            pass

        # First try with the cookie, then the full sequence
        if self._cookies:
            for url in ['https://m-api01.verisure.com',
                        'https://m-api02.verisure.com']:
                try:
                    self._base_url = url
                    installations = self.get_installations()
                    if 'errors' not in installations:
                        return installations
                except Exception:
                    # This is "normal"
                    # But maybe an stderr print would be good?
                    pass

        # The login with stored cookies failed, try to get a new one
        for login_url in ['https://automation01.verisure.com/auth/login',
                          'https://automation02.verisure.com/auth/login']:
            try:
                response = requests.post(
                    login_url,
                    headers={'APPLICATION_ID': 'PS_PYTHON'},
                    auth=(self._username, self._password))
                with open(self._cookieFileName, 'wb') as f:
                    pickle.dump(response.cookies, f)
                self._cookies = response.cookies
                for url in ['https://m-api01.verisure.com',
                            'https://m-api02.verisure.com']:
                    self._base_url = url
                    installations = self.get_installations()
                    if 'errors' not in installations:
                        return installations
            except Exception:
                pass

        raise LoginError("Failed to log in")

    def request(self, *operations):
        response = requests.post(
            '{base_url}/graphql'.format(base_url=self._base_url),
            headers={
                'APPLICATION_ID': 'PS_PYTHON',
                'Accept': 'application/json'},
            cookies=self._cookies,
            data=json.dumps(list(operations))
        )
        if response.status_code != 200:
            raise ResponseError(response.status_code, response.text)
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
                 code: VariableTypes.Code):
        """Set arm status away"""
        return {
            "operationName": "armAway",
            "variables": {
                "giid": self._giid,
                "code": code},
            "query": "mutation armAway($giid: String!, $code: String!) {\n  armStateArmAway(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def arm_home(self,
                 code: VariableTypes.Code):
        """Set arm state home"""
        return {
            "operationName": "armHome",
            "variables": {
                "giid": self._giid,
                "code": code},
            "query": "mutation armHome($giid: String!, $code: String!) {\n  armStateArmHome(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def arm_state(self):
        """Read arm state"""
        return {
            "operationName": "ArmState",
            "variables": {
                "giid": self._giid},
            "query": "query ArmState($giid: String!) {\n  installation(giid: $giid) {\n    armState {\n      type\n      statusType\n      date\n      name\n      changedVia\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def broadband(self):
        """Get broadband status"""
        return {
            "operationName": "Broadband",
            "variables": {
                "giid": self._giid},
            "query": "query Broadband($giid: String!) {\n  installation(giid: $giid) {\n    broadband {\n      testDate\n      isBroadbandConnected\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def capability(self):
        """Get capability"""
        return {
            "operationName": "Capability",
            "variables": {
                "giid": self._giid},
            "query": "query Capability($giid: String!) {\n  installation(giid: $giid) {\n    capability {\n      current\n      gained {\n        capability\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def charge_sms(self):
        """Charge SMS"""
        return {
            "operationName": "ChargeSms",
            "variables": {
                "giid": self._giid},
            "query": "query ChargeSms($giid: String!) {\n  installation(giid: $giid) {\n    chargeSms {\n      chargeSmartPlugOnOff\n      chargeLockUnlock\n      chargeArmDisarm\n      chargeNotifications\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def climate(self):
        """Get climate"""
        return {
            "operationName": "Climate",
            "variables": {
                "giid": self._giid},
            "query": "query Climate($giid: String!) {\n  installation(giid: $giid) {\n    climates {\n      device {\n        deviceLabel\n        area\n        gui {\n          label\n          __typename\n        }\n        __typename\n      }\n      humidityEnabled\n      humidityTimestamp\n      humidityValue\n      temperatureTimestamp\n      temperatureValue\n      thresholds {\n        aboveMaxAlert\n        belowMinAlert\n        sensorType\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def disarm(self,
               code: VariableTypes.Code):
        """Disarm alarm"""
        return {
            "operationName": "disarm",
            "variables": {
                "giid": self._giid,
                "code": code},
            "query": "mutation disarm($giid: String!, $code: String!) {\n  armStateDisarm(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def door_lock(self,
                  deviceLabel: VariableTypes.DeviceLabel,
                  code: VariableTypes.Code):
        """Get door lock status"""
        return {
            "operationName": "DoorLock",
            "variables": {
                "giid": self._giid,
                "deviceLabel": deviceLabel,
                "input": {
                    "code": code,
                },
            },
            "query": "mutation DoorLock($giid: String!, $deviceLabel: String!, $input: LockDoorInput!) {\n  DoorLock(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_lock_configuration(self,
                                deviceLabel: VariableTypes.DeviceLabel):
        """Get door lock configuration"""
        return {
            "operationName": "DoorLockConfiguration",
            "variables": {
                "giid": self._giid,
                "deviceLabel": deviceLabel},
            "query": "query DoorLockConfiguration($giid: String!, $deviceLabel: String!) {\n  installation(giid: $giid) {\n    smartLocks(filter: {deviceLabels: [$deviceLabel]}) {\n      device {\n        area\n        deviceLabel\n        __typename\n      }\n      configuration {\n        ... on YaleLockConfiguration {\n          autoLockEnabled\n          voiceLevel\n          volume\n          __typename\n        }\n        ... on DanaLockConfiguration {\n          holdBackLatchDuration\n          twistAssistEnabled\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def set_autolock_enabled(self,
                             deviceLabel: VariableTypes.DeviceLabel,
                             autoLockEnabled: bool):
        """Enable or disable autolock"""
        return {
            "operationName": "DoorLockUpdateConfig",
            "variables": {
                "giid": self._giid,
                "deviceLabel": deviceLabel,
                "input": {
                    "autoLockEnabled": autoLockEnabled
                }
            },
            "query": "mutation DoorLockUpdateConfig($giid: String!, $deviceLabel: String!, $input: DoorLockUpdateConfigInput!) {\n  DoorLockUpdateConfig(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_unlock(self,
                    deviceLabel: VariableTypes.DeviceLabel,
                    code: VariableTypes.Code):
        """Unlock door"""
        return {
            "operationName": "DoorUnlock",
            "variables": {
                "giid": self._giid,
                "deviceLabel": deviceLabel,
                "input": {
                    "code": code,
                },
            },
            "query": "mutation DoorUnlock($giid: String!, $deviceLabel: String!, $input: LockDoorInput!) {\n  DoorUnlock(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_window(self):
        """Read status of door and window sensors"""
        return {
            "operationName": "DoorWindow",
            "variables": {
                "giid": self._giid},
            "query": "query DoorWindow($giid: String!) {\n  installation(giid: $giid) {\n    doorWindows {\n      device {\n        deviceLabel\n        __typename\n      }\n      type\n      area\n      state\n      wired\n      reportTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def event_log(self):
        """Read event log"""
        return {
            "operationName": "EventLog",
            "variables": {
                "giid": self._giid,
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
    def guardian_sos(self):
        """Guardian SOS"""
        return {
            "operationName": "GuardianSos",
            "variables": {},
            "query": "query GuardianSos {\n  guardianSos {\n    serverTime\n    sos {\n      fullName\n      phone\n      deviceId\n      deviceName\n      giid\n      type\n      username\n      expireDate\n      warnBeforeExpireDate\n      contactId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def is_guardian_activated(self):
        """Is guardian activated"""
        return {
            "operationName": "IsGuardianActivated",
            "variables": {
                "giid": self._giid,
                "featureName": "GUARDIAN"},
            "query": "query IsGuardianActivated($giid: String!, $featureName: String!) {\n  installation(giid: $giid) {\n    activatedFeature {\n      isFeatureActivated(featureName: $featureName)\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def permissions(self):
        """Permissions"""
        return {
            "operationName": "Permissions",
            "variables": {
                "giid": self._giid,
                "email": self._username},
            "query": "query Permissions($giid: String!, $email: String!) {\n  permissions(giid: $giid, email: $email) {\n    accountPermissionsHash\n    name\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def poll_arm_state(self,
                       transactionId: VariableTypes.TransactionId,
                       futureState: VariableTypes.ArmFutureState):
        """Poll arm state"""
        return {
            "operationName": "pollArmState",
            "variables": {
                "giid": self._giid,
                "transactionId": transactionId,
                "futureState": futureState},
            "query": "query pollArmState($giid: String!, $transactionId: String, $futureState: ArmStateStatusTypes!) {\n  installation(giid: $giid) {\n    armStateChangePollResult(transactionId: $transactionId, futureState: $futureState) {\n      result\n      createTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def poll_lock_state(self,
                        transactionId: VariableTypes.TransactionId,
                        deviceLabel: VariableTypes.DeviceLabel,
                        futureState: VariableTypes.LockFutureState):
        """Poll lock state"""
        return {
            "operationName": "pollLockState",
            "variables": {
                "giid": self._giid,
                "transactionId": transactionId,
                "deviceLabel": deviceLabel,
                "futureState": futureState},
            "query": "query pollLockState($giid: String!, $transactionId: String, $deviceLabel: String!, $futureState: DoorLockState!) {\n  installation(giid: $giid) {\n    doorLockStateChangePollResult(transactionId: $transactionId, deviceLabel: $deviceLabel, futureState: $futureState) {\n      result\n      createTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def remaining_sms(self):
        """Get remaing number of SMS"""
        return {
            "operationName": "RemainingSms",
            "variables": {
                "giid": self._giid},
            "query": "query RemainingSms($giid: String!) {\n  installation(giid: $giid) {\n    remainingSms\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def smart_button(self):
        """Get smart button state"""
        return {
            "operationName": "SmartButton",
            "variables": {
                "giid": self._giid},
            "query": "query SmartButton($giid: String!) {\n  installation(giid: $giid) {\n    smartButton {\n      entries {\n        smartButtonId\n        icon\n        label\n        color\n        active\n        action {\n          actionType\n          expectedState\n          target {\n            ... on Installation {\n              alias\n              __typename\n            }\n            ... on Device {\n              deviceLabel\n              area\n              gui {\n                label\n                __typename\n              }\n              featureStatuses(type: \"SmartPlug\") {\n                device {\n                  deviceLabel\n                  __typename\n                }\n                ... on SmartPlug {\n                  icon\n                  isHazardous\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def smart_lock(self):
        """Get smart lock state"""
        return {
            "operationName": "SmartLock",
            "variables": {
                "giid": self._giid},
            "query": "query SmartLock($giid: String!) {\n  installation(giid: $giid) {\n    smartLocks {\n      lockStatus\n      doorState\n      lockMethod\n      eventTime\n      doorLockType\n      secureMode\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      user {\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def set_smartplug(self,
                      deviceLabel: VariableTypes.DeviceLabel,
                      state: bool):
        """Set state of smart plug"""
        return {
            "operationName": "UpdateState",
            "variables": {
                "giid": self._giid,
                "deviceLabel": deviceLabel,
                "state": state},
            "query": "mutation UpdateState($giid: String!, $deviceLabel: String!, $state: Boolean!) {\n  SmartPlugSetState(giid: $giid, input: [{deviceLabel: $deviceLabel, state: $state}])}",  # noqa: E501
        }

    @query_func
    def smartplug(self,
                  deviceLabel: VariableTypes.DeviceLabel):
        """Read status of a single smart plug"""
        return {
            "operationName": "SmartPlug",
            "variables": {
                "giid": self._giid,
                "deviceLabel": deviceLabel},
            "query": "query SmartPlug($giid: String!, $deviceLabel: String!) {\n  installation(giid: $giid) {\n    smartplugs(filter: {deviceLabels: [$deviceLabel]}) {\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      currentState\n      icon\n      isHazardous\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def smartplugs(self):
        """Read status of all smart plugs"""
        return {
            "operationName": "SmartPlug",
            "variables": {
                "giid": self._giid},
            "query": "query SmartPlug($giid: String!) {\n  installation(giid: $giid) {\n    smartplugs {\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      currentState\n      icon\n      isHazardous\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def user_trackings(self):
        """Read user tracking status"""
        return {
            "operationName": "userTrackings",
            "variables": {
                "giid": self._giid},
            "query": "query userTrackings($giid: String!) {\n  installation(giid: $giid) {\n    userTrackings {\n      isCallingUser\n      webAccount\n      status\n      xbnContactId\n      currentLocationName\n      deviceId\n      name\n      initials\n      currentLocationTimestamp\n      deviceName\n      currentLocationId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def cameras(self):
        """Get cameras state"""
        return {
            "operationName": "Camera",
            "variables": {
                "all": True,
                "giid": self._giid},
            "query": "query Camera($giid: String!, $all: Boolean!) {\n    installation(giid: $giid) {\n        cameras(allCameras: $all) {\n            visibleOnCard\n            initiallyConfigured\n            imageCaptureAllowed\n            imageCaptureAllowedByArmstate\n            device {\n        deviceLabel\n        area\n        __typename\n      }\n            latestCameraSeries {\n                image {\n                    imageId\n                    imageStatus\n                    captureTime\n                    url\n                }\n            }\n        }\n    }\n}",  # noqa: E501
            }

    @query_func
    def cameras_last_image(self):
        """Get cameras last image"""
        return {
            "variables": {
                "giid": self._giid},
            "query": "query queryCaptureImageRequestStatus($giid: String!) {\n  installation(giid: $giid) {\n    cameraContentProvider {\n      latestImage {\n        deviceLabel\n        mediaId\n        contentType\n        contentUrl\n        timestamp\n        duration\n        thumbnailUrl\n        bitRate\n        width\n        height\n        codec\n      }\n    }\n  }\n}",  # noqa: E501
            }

    @query_func
    def camera_get_requestId(self,
                             deviceLabel: VariableTypes.DeviceLabel):
        """Get requestId for camera_capture"""
        return {
            "variables": {
                "deviceIdentifier": "RandomString",
                "deviceLabel": deviceLabel,
                "giid": self._giid,
                "resolution": "high"},
            "query": "mutation cccp($giid: String!, $deviceLabel: String!, $resolution: String!, $deviceIdentifier: String) {\n  ContentProviderCaptureImageRequest(giid: $giid, deviceLabel: $deviceLabel, resolution: $resolution, deviceIdentifier: $deviceIdentifier) {\n    requestId\n  }\n}",  # noqa: E501
            }

    @query_func
    def camera_capture(self,
                       deviceLabel: VariableTypes.DeviceLabel,
                       requestId: VariableTypes.RequestId):
        """Capture a new image from a camera"""
        return {
            "variables": {
                "deviceLabel": deviceLabel,
                "giid": self._giid,
                "requestId": requestId},
            "query": "query queryCaptureImageRequestStatus($giid: String!, $deviceLabel: String!, $requestId: BigInt!) {\n  installation(giid: $giid) {\n    cameraContentProvider {\n      captureImageRequestStatus(deviceLabel: $deviceLabel, requestId: $requestId) {\n        mediaRequestStatus\n      }\n    }\n  }\n}",  # noqa: E501
            }
