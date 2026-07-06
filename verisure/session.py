'''
Verisure session, using verisure app api
'''

import json
import logging
import os
import pickle
import time
from typing import Any, Callable, Dict, Optional, Tuple

import requests

LOGGER = logging.getLogger(__package__)


class Error(Exception):
    ''' Verisure session error '''


class RequestError(Error):
    ''' Network or transport failure '''


class LoginError(Error):
    ''' Login failed '''

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(LoginError):
    ''' Credentials rejected or session expired '''


class CookieReadError(LoginError):
    ''' Cookie file missing or corrupt '''


class RateLimitError(Error):
    ''' API rate limit exceeded '''


class LogoutError(Error):
    ''' Logout failed '''


class ResponseError(Error):
    ''' Unexpected response '''

    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
        super().__init__(
            f'Invalid response, status code: {status_code} - Data: {text}')


MFA_REQUIRED_MESSAGE = (
    'Multifactor authentication enabled, disable or create MFA cookie'
)


def _response_signals_rate_limit(text: str) -> bool:
    """Return True when the API rejected the call for rate or quota limits."""
    lower = text.lower()
    return (
        'aut_00021' in lower
        or 'acc_00002' in lower
        or 'toomanystepuptokens' in lower
        or 'too many step up tokens' in lower
        or 'request limit' in lower
        or 'rate limit' in lower
        or 'too many requests' in lower
    )


def _http_error_from_response(status_code: int, text: str) -> Error:
    """Map an HTTP error response to a structured Verisure exception."""
    if status_code == 429 or _response_signals_rate_limit(text):
        return RateLimitError(text)
    if status_code in (401, 403):
        return AuthenticationError(text, status_code=status_code)
    if status_code >= 500:
        return ResponseError(status_code, text)
    return LoginError(text, status_code=status_code)


def query_func(func: Callable[..., Any]) -> Callable[..., Any]:
    """A wrapper that indicates that the function is a query (used by CLI)"""
    setattr(func, 'is_query', True)
    return func


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
        username (str): Username used to login to verisure app.
        password (str): Password used to login to verisure app.
        cookie_file_name (str): path to cookie file.
        request_timeout (Tuple[float, float]): connect/read timeout in seconds.
    """

    def __init__(self, username: str, password: str,
                 cookie_file_name: str = '~/.verisure-cookie',
                 request_timeout: Tuple[float, float] = (10.0, 30.0)):
        LOGGER.info(f"Initialize Session ({username=}, {cookie_file_name=})")
        self._username = username
        self._password = password
        self._cookies = None
        self._cookie_file_name = os.path.expanduser(cookie_file_name)
        self._request_timeout = request_timeout
        self._trust_token = None
        self._mfa_login_pending = False
        self._giid: Optional[str] = None
        self._base_url = None
        self._base_urls = ['https://automation01.verisure.com',
                           'https://automation02.verisure.com']
        self._post = self._wrap_request(requests.post)
        self._delete = self._wrap_request(requests.delete)
        self._get = self._wrap_request(requests.get)

    def _resolve_giid(self, giid: Optional[VariableTypes.Giid] = None) -> str:
        resolved_giid = giid or self._giid
        if resolved_giid is None:
            raise ValueError("Set default giid or pass explicit")
        return resolved_giid


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
                    kwargs.setdefault('timeout', self._request_timeout)
                    response = function(base_url+url, *args, **kwargs)
                    if response.status_code > 200 or "errors" in response.text:
                        LOGGER.debug(
                            f"{response.request.method} {response.request.url} "
                            f"{response.status_code} f{response.text}"
                        )
                    if response.status_code >= 500:
                        last_exception = ResponseError(
                            response.status_code, response.text)
                        self._base_urls.reverse()
                        continue
                    if response.status_code >= 400:
                        last_exception = _http_error_from_response(
                            response.status_code, response.text)
                        break
                    if response.status_code == 200:
                        if _response_signals_rate_limit(response.text):
                            raise RateLimitError(response.text)
                        if "SYS_00004" in response.text:
                            self._base_urls.reverse()
                            continue
                        return response
 
                except requests.exceptions.RequestException as ex:
                    LOGGER.warning(f"Unexpected error on '{base_url}{url}' ({ex=})")
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
            self._cookies = response.cookies
            self._mfa_login_pending = True
            raise LoginError(MFA_REQUIRED_MESSAGE)

        self._mfa_login_pending = False
        self._cookies = response.cookies
        with open(self._cookie_file_name, 'wb') as f:
            pickle.dump(self._cookies, f)

        installations = self.get_installations()
        if 'errors' not in installations:
            return installations

        raise LoginError("Failed to log in")

    def request_mfa(self):
        """ Request MFA verification code """

        if not self._mfa_login_pending:
            response = self._post(
                url="/auth/login",
                headers={'APPLICATION_ID': 'PS_PYTHON'},
                auth=(self._username, self._password))

            if "stepUpToken" not in response.text:
                raise LoginError("Multifactor authentication disabled, "
                                 "use regular login instead")

            self._cookies = response.cookies
            self._mfa_login_pending = True

        self._mfa_login_pending = False
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

        trust_response = self._post(
            url="/auth/trust",
            headers={
                'APPLICATION_ID': 'PS_PYTHON',
                'Accept': 'application/json',
            },
            cookies=self._cookies)
        self._cookies.update(trust_response.cookies)
        with open(self._cookie_file_name, 'wb') as cookie_file:
            pickle.dump(self._cookies, cookie_file)
        self._trust_token = trust_response.json()

        installations = self.get_installations()
        if 'errors' not in installations:
            return installations

        raise LoginError("Failed to log in")

    def _load_cookie_file_into_memory(self):
        """Populate ``_cookies`` from the persisted pickle (used by cookie login paths)."""

        try:
            with open(self._cookie_file_name, 'rb') as cookie_file:
                self._cookies = pickle.load(cookie_file)
        except OSError as ex:
            raise CookieReadError("Failed to read cookie") from ex
        except (EOFError, pickle.UnpicklingError, AttributeError, TypeError, ValueError) as ex:
            raise CookieReadError("Failed to read cookie") from ex

    def _update_cookie_once(self):
        """Refresh the session cookie once via ``/auth/token``."""
        if self._cookies is None:
            self._load_cookie_file_into_memory()

        cookie_jar = requests.sessions.RequestsCookieJar()
        if self._cookies is not None:
            for name, value in self._cookies.items():
                if name in ['vid', 'vs-refresh']:
                    cookie_jar[name] = value
        response = self._get(
            url="/auth/token",
            headers={'APPLICATION_ID': 'PS_PYTHON'},
            cookies=cookie_jar)

        self._cookies.update(response.cookies)
        with open(self._cookie_file_name, 'wb') as cookie_file:
            pickle.dump(self._cookies, cookie_file)
        LOGGER.debug(f"Saved cookies: {[cookie for cookie in self._cookies.keys()]}")

    def update_cookie(self, attempts=3, delay=1.0):
        """ Update expired cookie
        Cookie can last 15 minutes before it needs to be updated.

        Retries token refresh when the API returns a recoverable login error.
        Authentication and cookie-read failures are raised immediately.

        Long-running callers may reset ``self._cookies`` while a valid pickle remains
        on disk; hydrate from the file before calling ``/auth/token`` so the request
        is not sent with an empty cookie jar.
        """
        last_login_error = None
        for attempt in range(attempts):
            try:
                self._update_cookie_once()
                return
            except LoginError as ex:
                if isinstance(ex, (AuthenticationError, CookieReadError)):
                    raise
                last_login_error = ex
                if attempt + 1 < attempts:
                    LOGGER.debug(
                        "Cookie refresh login error attempt %s, retrying: %s",
                        attempt + 1,
                        ex,
                    )
                    time.sleep(delay)
                    continue
                raise
        if last_login_error is not None:
            raise last_login_error

    def login_cookie(self):
        """ Login using cookie
        Return installations
        """

        self._load_cookie_file_into_memory()

        # Login
        cookie_jar = requests.sessions.RequestsCookieJar()
        for name, value in self._cookies.items():
            if 'vs-trust' in name:
                cookie_jar.set(name, value)
        response = self._post(
            url="/auth/login",
            headers={'APPLICATION_ID': 'PS_PYTHON'},
            auth=(self._username, self._password),
            cookies=cookie_jar)
        self._cookies.update(response.cookies)
        with open(self._cookie_file_name, 'wb') as f:
            pickle.dump(self._cookies, f)

        installations = self.get_installations()
        if 'errors' not in installations:
            return installations

        raise LoginError("Failed to log in")

    def logout(self):
        """ Log out from the verisure app api """
        try:
            if self._trust_token is not None:
                token = self._trust_token['trustTokenValue']
                self._delete(
                    url=f"/auth/trust/{token}",
                    headers={
                        'APPLICATION_ID': 'PS_PYTHON',
                        'Accept': 'application/json',
                    },
                    cookies=self._cookies)
            self._delete(
                url="/auth/logout",
                headers={'APPLICATION_ID': 'PS_PYTHON'},
                cookies=self._cookies)
        finally:
            self._base_url = None
            self._giid = None
            self._cookies = None
            self._trust_token = None
            self._mfa_login_pending = False
            if os.path.exists(self._cookie_file_name):
                os.remove(self._cookie_file_name)

    def request(self, *operations):
        """Request operations"""
        if not operations:
            # Return empty json if no operations were requested
            return json.loads("{}")
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

    def set_giid(self, giid: VariableTypes.Giid):
        """ Set installation giid

        Args:
            giid (str): Installation identifier
        """
        self._giid = giid
        LOGGER.info(f"Installation identifier set ({giid=})")

    @query_func
    def arm_away(self,
                 code: VariableTypes.Code,
                 giid: Optional[VariableTypes.Giid] = None,
                 force_arm: bool=False) -> Dict[str, object]:
        """Set arm status away"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "armAway",
            "variables": {
                "giid": resolved_giid,
                "code": code,
                "forceArm": force_arm},
            "query": "mutation armAway($giid: String!, $code: String!, $forceArm: Boolean) {\n  armStateArmAway(giid: $giid, code: $code, forceArm: $forceArm)\n}\n",  # noqa: E501
        }

    @query_func
    def arm_home(self,
                 code: VariableTypes.Code,
                 giid: Optional[VariableTypes.Giid] = None,
                 force_arm: bool=False) -> Dict[str, object]:
        """Set arm state home"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "armHome",
            "variables": {
                "giid": resolved_giid,
                "code": code,
                "forceArm": force_arm},
            "query": "mutation armHome($giid: String!, $code: String!, $forceArm: Boolean) {\n  armStateArmHome(giid: $giid, code: $code, forceArm: $forceArm)\n}\n",  # noqa: E501
        }

    @query_func
    def arm_state(self,
                  giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Read arm state"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "ArmState",
            "variables": {
                "giid": resolved_giid},
            "query": "query ArmState($giid: String!) {\n  installation(giid: $giid) {\n    armState {\n      type\n      statusType\n      date\n      name\n      changedVia\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def broadband(self,
                  giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get broadband status"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "Broadband",
            "variables": {
                "giid": resolved_giid},
            "query": "query Broadband($giid: String!) {\n  installation(giid: $giid) {\n    broadband {\n      testDate\n      isBroadbandConnected\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def capability(self,
                   giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get capability"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "Capability",
            "variables": {
                "giid": resolved_giid},
            "query": "query Capability($giid: String!) {\n  installation(giid: $giid) {\n    capability {\n      current\n      gained {\n        capability\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def charge_sms(self,
                   giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Charge SMS"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "ChargeSms",
            "variables": {
                "giid": resolved_giid},
            "query": "query ChargeSms($giid: String!) {\n  installation(giid: $giid) {\n    chargeSms {\n      chargeSmartPlugOnOff\n      chargeLockUnlock\n      chargeArmDisarm\n      chargeNotifications\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def climate(self,
                giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get climate"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "Climate",
            "variables": {
                "giid": resolved_giid},
            "query": "query Climate($giid: String!) {\n  installation(giid: $giid) {\n    climates {\n      device {\n        deviceLabel\n        area\n        gui {\n          label\n          __typename\n        }\n        __typename\n      }\n      humidityEnabled\n      humidityTimestamp\n      humidityValue\n      temperatureTimestamp\n      temperatureValue\n      thresholds {\n        aboveMaxAlert\n        belowMinAlert\n        sensorType\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def disarm(self,
               code: VariableTypes.Code,
               giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Disarm alarm"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "disarm",
            "variables": {
                "giid": resolved_giid,
                "code": code},
            "query": "mutation disarm($giid: String!, $code: String!) {\n  armStateDisarm(giid: $giid, code: $code)\n}\n",  # noqa: E501
        }

    @query_func
    def door_lock(self,
                  device_label: VariableTypes.DeviceLabel,
                  code: VariableTypes.Code,
                  giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Lock door"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "DoorLock",
            "variables": {
                "giid": resolved_giid,
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
                                giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get door lock configuration"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "DoorLockConfiguration",
            "variables": {
                "giid": resolved_giid,
                "deviceLabel": device_label},
            "query": "query DoorLockConfiguration($giid: String!, $deviceLabel: String!) {\n  installation(giid: $giid) {\n    smartLocks(filter: {deviceLabels: [$deviceLabel]}) {\n      device {\n        area\n        deviceLabel\n        __typename\n      }\n      configuration {\n        ... on YaleLockConfiguration {\n          autoLockEnabled\n          voiceLevel\n          volume\n          __typename\n        }\n        ... on DanaLockConfiguration {\n          holdBackLatchDuration\n          twistAssistEnabled\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def set_autolock_enabled(self,
                             device_label: VariableTypes.DeviceLabel,
                             auto_lock_enabled: bool,
                             giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Enable or disable autolock"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "DoorLockUpdateConfig",
            "variables": {
                "giid": resolved_giid,
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
                    giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Unlock door"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "DoorUnlock",
            "variables": {
                "giid": resolved_giid,
                "deviceLabel": device_label,
                "input": {
                    "code": code,
                },
            },
            "query": "mutation DoorUnlock($giid: String!, $deviceLabel: String!, $input: LockDoorInput!) {\n  DoorUnlock(giid: $giid, deviceLabel: $deviceLabel, input: $input)\n}\n",  # noqa: E501
        }

    @query_func
    def door_window(self,
                    giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Read status of door and window sensors"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "DoorWindow",
            "variables": {
                "giid": resolved_giid},
            "query": "query DoorWindow($giid: String!) {\n  installation(giid: $giid) {\n    doorWindows {\n      device {\n        deviceLabel\n        __typename\n      }\n      type\n      area\n      state\n      wired\n      reportTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def event_log(self,
                  giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Read event log"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "EventLog",
            "variables": {
                "giid": resolved_giid,
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
    def fetch_all_installations(self) -> Dict[str, object]:
        """Fetch installations"""
        return {
            "operationName": "fetchAllInstallations",
            "variables": {
                "email": self._username},
            "query": "query fetchAllInstallations($email: String!){\n  account(email: $email) {\n    installations {\n      giid\n      alias\n      customerType\n      dealerId\n      subsidiary\n      pinCodeLength\n      locale\n      address {\n        street\n        city\n        postalNumber\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }
    
    @query_func
    def firmware(self,
                 giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get firmware information"""
        resolved_giid = self._resolve_giid(giid)
        return {
	        "operationName": "Firmware",
	        "variables": {
		        "giid": resolved_giid
	        },
	        "query": "query Firmware($giid: String!) {\n  installation(giid: $giid) {\n    firmware {\n      status {\n        latestFirmware\n        requestedFirmware\n        upgradeable\n        status\n        gateways {\n          reportedRunningFirmware\n          deviceLabel\n          status\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n" # noqa: E501
        }

    @query_func
    def guardian_sos(self) -> Dict[str, object]:
        """Guardian SOS"""
        return {
            "operationName": "GuardianSos",
            "variables": {},
            "query": "query GuardianSos {\n  guardianSos {\n    serverTime\n    sos {\n      fullName\n      phone\n      deviceId\n      deviceName\n      giid\n      type\n      username\n      expireDate\n      warnBeforeExpireDate\n      contactId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def is_guardian_activated(self,
                              giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Is guardian activated"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "IsGuardianActivated",
            "variables": {
                "giid": resolved_giid,
                "featureName": "GUARDIAN"},
            "query": "query IsGuardianActivated($giid: String!, $featureName: String!) {\n  installation(giid: $giid) {\n    activatedFeature {\n      isFeatureActivated(featureName: $featureName)\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def permissions(self,
                    giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Permissions"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "Permissions",
            "variables": {
                "giid": resolved_giid,
                "email": self._username},
            "query": "query Permissions($giid: String!, $email: String!) {\n  permissions(giid: $giid, email: $email) {\n    accountPermissionsHash\n    name\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def poll_arm_state(self,
                       transaction_id: VariableTypes.TransactionId,
                       future_state: VariableTypes.ArmFutureState,
                       giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Poll arm state"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "pollArmState",
            "variables": {
                "giid": resolved_giid,
                "transactionId": transaction_id,
                "futureState": future_state},
            "query": "query pollArmState($giid: String!, $transactionId: String, $futureState: ArmStateStatusTypes!) {\n  installation(giid: $giid) {\n    armStateChangePollResult(transactionId: $transactionId, futureState: $futureState) {\n      result\n      createTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def poll_lock_state(self,
                        transaction_id: VariableTypes.TransactionId,
                        device_label: VariableTypes.DeviceLabel,
                        future_state: VariableTypes.LockFutureState,
                        giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Poll lock state"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "pollLockState",
            "variables": {
                "giid": resolved_giid,
                "transactionId": transaction_id,
                "deviceLabel": device_label,
                "futureState": future_state},
            "query": "query pollLockState($giid: String!, $transactionId: String, $deviceLabel: String!, $futureState: DoorLockState!) {\n  installation(giid: $giid) {\n    doorLockStateChangePollResult(transactionId: $transactionId, deviceLabel: $deviceLabel, futureState: $futureState) {\n      result\n      createTime\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def remaining_sms(self,
                      giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get remaing number of SMS"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "RemainingSms",
            "variables": {
                "giid": resolved_giid},
            "query": "query RemainingSms($giid: String!) {\n  installation(giid: $giid) {\n    remainingSms\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def smart_button(self,
                     giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get smart button state"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "SmartButton",
            "variables": {
                "giid": resolved_giid},
            "query": "query SmartButton($giid: String!) {\n  installation(giid: $giid) {\n    smartButton {\n      entries {\n        smartButtonId\n        icon\n        label\n        color\n        active\n        action {\n          actionType\n          expectedState\n          target {\n            ... on Installation {\n              alias\n              __typename\n            }\n            ... on Device {\n              deviceLabel\n              area\n              gui {\n                label\n                __typename\n              }\n              featureStatuses(type: \"SmartPlug\") {\n                device {\n                  deviceLabel\n                  __typename\n                }\n                ... on SmartPlug {\n                  icon\n                  isHazardous\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def smart_lock(self,
                   giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get smart lock state"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "SmartLock",
            "variables": {
                "giid": resolved_giid},
            "query": "query SmartLock($giid: String!) {\n  installation(giid: $giid) {\n    smartLocks {\n      lockStatus\n      doorState\n      lockMethod\n      eventTime\n      doorLockType\n      secureMode\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      user {\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
        }

    @query_func
    def set_smartplug(self,
                      device_label: VariableTypes.DeviceLabel,
                      state: bool,
                      giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Set state of smart plug"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "UpdateState",
            "variables": {
                "giid": resolved_giid,
                "deviceLabel": device_label,
                "state": state},
            "query": "mutation UpdateState($giid: String!, $deviceLabel: String!, $state: Boolean!) {\n  SmartPlugSetState(giid: $giid, input: [{deviceLabel: $deviceLabel, state: $state}])}",  # noqa: E501
        }

    @query_func
    def smartplug(self,
                  device_label: VariableTypes.DeviceLabel,
                  giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Read status of a single smart plug"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "SmartPlug",
            "variables": {
                "giid": resolved_giid,
                "deviceLabel": device_label},
            "query": "query SmartPlug($giid: String!, $deviceLabel: String!) {\n  installation(giid: $giid) {\n    smartplugs(filter: {deviceLabels: [$deviceLabel]}) {\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      currentState\n      icon\n      isHazardous\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def smartplugs(self,
                   giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Read status of all smart plugs"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "SmartPlug",
            "variables": {
                "giid": resolved_giid},
            "query": "query SmartPlug($giid: String!) {\n  installation(giid: $giid) {\n    smartplugs {\n      device {\n        deviceLabel\n        area\n        __typename\n      }\n      currentState\n      icon\n      isHazardous\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def user_trackings(self,
                       giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Read user tracking status"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "userTrackings",
            "variables": {
                "giid": resolved_giid},
            "query": "query userTrackings($giid: String!) {\n  installation(giid: $giid) {\n    userTrackings {\n      isCallingUser\n      webAccount\n      status\n      xbnContactId\n      currentLocationName\n      deviceId\n      name\n      initials\n      currentLocationTimestamp\n      deviceName\n      currentLocationId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
            }

    @query_func
    def cameras(self,
                giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get cameras state"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "Camera",
            "variables": {
                "all": True,
                "giid": resolved_giid},
            "query": "query Camera($giid: String!, $all: Boolean!) {\n    installation(giid: $giid) {\n        cameras(allCameras: $all) {\n            visibleOnCard\n            initiallyConfigured\n            imageCaptureAllowed\n            imageCaptureAllowedByArmstate\n            device {\n        deviceLabel\n        area\n        __typename\n      }\n            latestCameraSeries {\n                image {\n                    imageId\n                    imageStatus\n                    captureTime\n                    url\n                }\n            }\n        }\n    }\n}",  # noqa: E501
            }

    @query_func
    def cameras_last_image(self,
                           giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get cameras last image"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "variables": {
                "giid": resolved_giid},
            "query": "query queryCaptureImageRequestStatus($giid: String!) {\n  installation(giid: $giid) {\n    cameraContentProvider {\n      latestImage {\n        deviceLabel\n        mediaId\n        contentType\n        contentUrl\n        timestamp\n        duration\n        thumbnailUrl\n        bitRate\n        width\n        height\n        codec\n      }\n    }\n  }\n}",  # noqa: E501
            }

    @query_func
    def cameras_image_series(self, 
                             limit: int = 50,
                             offset: int = 0,
                             giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get the cameras image series"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "operationName": "GQL_CCCP_SearchMedia",
            "variables": {
                "giid": resolved_giid,
                "limit": limit,
                "offset": offset},
            "query": "mutation GQL_CCCP_SearchMedia(\n	$giid: BigInt!\n	$offset: Int\n	$limit: Int\n	$fromDate: Date\n	$toDate: Date) {\n\n	ContentProviderMediaSearch(\n		giid: $giid\n		offset: $offset\n		limit: $limit\n		fromDate: $fromDate\n		toDate: $toDate\n	) {\n		totalNumberOfMediaSeries\n		mediaSeriesList {\n			seriesId\n			storageType\n			viewed\n			timestamp\n			deviceMediaList {\n				contentUrl\n				mediaAvailable\n				deviceLabel\n				mediaId\n				contentType\n				timestamp\n				requestTimestamp\n				duration\n				expiryDate\n				viewed\n				thumbnailUrl\n				bitRate\n				width\n				height\n				codec\n			}\n		}\n	}\n}",  # noqa: E501}
        }

    @query_func
    def camera_get_request_id(self,
                             device_label: VariableTypes.DeviceLabel,
                             giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Get requestId for camera_capture"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "variables": {
                "deviceIdentifier": "RandomString",
                "deviceLabel": device_label,
                "giid": resolved_giid,
                "resolution": "high"},
            "query": "mutation cccp($giid: String!, $deviceLabel: String!, $resolution: String!, $deviceIdentifier: String) {\n  ContentProviderCaptureImageRequest(giid: $giid, deviceLabel: $deviceLabel, resolution: $resolution, deviceIdentifier: $deviceIdentifier) {\n    requestId\n  }\n}",  # noqa: E501
            }

    @query_func
    def camera_capture(self,
                       device_label: VariableTypes.DeviceLabel,
                       request_id: VariableTypes.RequestId,
                       giid: Optional[VariableTypes.Giid] = None) -> Dict[str, object]:
        """Capture a new image from a camera"""
        resolved_giid = self._resolve_giid(giid)
        return {
            "variables": {
                "deviceLabel": device_label,
                "giid": resolved_giid,
                "requestId": request_id},
            "query": "query queryCaptureImageRequestStatus($giid: String!, $deviceLabel: String!, $requestId: BigInt!) {\n  installation(giid: $giid) {\n    cameraContentProvider {\n      captureImageRequestStatus(deviceLabel: $deviceLabel, requestId: $requestId) {\n        mediaRequestStatus\n      }\n    }\n  }\n}",  # noqa: E501
            }

    def download_image(self, image_url: str, file_name: str) -> None:
        """Download image from url"""
        try:
            response = requests.get(image_url, stream=True, timeout=self._request_timeout)
        except requests.exceptions.RequestException as ex:
            raise RequestError("Failed to get image") from ex
        with open(file_name, 'wb') as image_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    image_file.write(chunk)
