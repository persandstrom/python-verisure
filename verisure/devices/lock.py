"""
Lock device
"""
import time

from .overview import Overview

OVERVIEW_URL = '/remotecontrol'
COMMAND_URL = '/remotecontrol/lockunlock.cmd'
AUTORELOCK_URL = '/settings/autorelock/'
SETAUTORELOCK_URL = '/settings/setautorelock.cmd'
CHECK_STATE = '/remotecontrol/checkstate.cmd'


class Lock(object):
    """ Lock device

    Args:
        session (verisure.session): Current session
    """

    def __init__(self, session):
        self._session = session

    def get(self):
        """ Get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('lock', val) for val in status
                if val['type'] == 'DOOR_LOCK']

    def set(self, code, device_id, state):
        """ set status of alarm component

            Args:
                code (str): Personal alarm code (four digits)
                device_id (str): lock device id
                state (str): 'LOCKED', or 'UNLOCKED'

        """
        data = {
            'code': code,
            'deviceLabel': device_id,
            'state': state
        }
        return not self._session.post(COMMAND_URL, data)

    def get_autorelock(self):
        """ Get autorelock status """
        return self._session.get(AUTORELOCK_URL)

    def set_autorelock(self, device_id, autorelock):
        """ Set autorelock enabled

            Args:
                device_id (str): lock device id
                autorelock (bool): True to set, else False
        """
        if autorelock:
            data = {
                "_csrf": self._session.csrf,
                "_doorLockDevices[0].autoRelockEnabled": "on",
                "doorLockDevices[0].autoRelockEnabled": "true",
                "enabledDoorLocks": device_id
            }
        else:
            data = {
                "_csrf": self._session.csrf,
                "_doorLockDevices[0].autoRelockEnabled": "on",
                "enabledDoorLocks": ""
            }
        return not self._session.post(SETAUTORELOCK_URL, data)

    def wait_while_pending(self, max_request_count=100):
        """ Wait for pending lockstatus to finish

            Args:
                max_request_count (int): maximum number of post requests

            Returns: retries if success else -1

        """

        for counter in range(max_request_count):
            data = {'counter': counter}
            response = self._session.post(CHECK_STATE, data)
            if 'hasResult' not in response:
                break
            if 'hasPending' in response and not response['hasPending']:
                return counter
            counter = counter + 1
            time.sleep(1)
        return -1
