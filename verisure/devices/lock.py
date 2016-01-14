"""
Lock device
"""

from .overview import Overview

OVERVIEW_URL = '/remotecontrol'
COMMAND_URL = '/remotecontrol/lockunlock.cmd'
AUTORELOCK_URL = '/settings/autorelock/'
SETAUTORELOCK_URL = '/settings/setautorelock.cmd'


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
        return self._session.get(AUTORELOCK_URL)

    def set_autorelock(self, device_id, autorelock):
        data = {
            "_csrf": self._session.csrf,
            "_doorLockDevices[0].autoRelockEnabled":
                "on" if autorelock else "off",
            "doorLockDevices[0].autoRelockEnabled":
                "true" if autorelock else "false",
            "enabledDoorLocks": device_id
        }
        return not self._session.post(SETAUTORELOCK_URL, data)
