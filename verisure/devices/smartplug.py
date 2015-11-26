"""
Smartplug device
"""

from .overview import Overview

OVERVIEW_URL = '/overview/smartplug'
COMMAND_URL = '/smartplugs/onoffplug.cmd'


class Smartplug(object):
    """ Smartplug device

    Args:
        session (verisure.session): Current session
    """

    def __init__(self, session):
        self._session = session

    def get(self):
        """ Get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('smartplug', val) for val in status]

    def set(self, device_id, value):
        """ Set device status

        Args:
            device_id (str): Id of the smartplug
            value (str): new status, 'on' or 'off'
        """
        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        return not self._session.post(COMMAND_URL, data)
