"""
Smartplug device
"""
import time

from .overview import Overview

OVERVIEW_URL = '/overview/smartplug'
COMMAND_URL = '/smartplugs/onoffplug.cmd'
SETTING_URL = '/settings/smartplug'


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

    def get_settings(self):
        return self._session.get(SETTING_URL)

    def set_location(self, device_id, location):
        details_url = '/smarthome/{}/details'.format(
            device_id.upper().replace(' ', '%20'))
        details = self._session.get(details_url)
        details['location'] = location
        self._session.put(details_url, details)

    def wait_while_updating(self, device_id, value, max_request_count=100):
        """ Wait for device status to update

        Args:
            device_id (str): Id of the smartplug
            value (str): status to wait for, 'on' or 'off'
            max_request_count (int): maximum number of post requests

            Returns: retries if success else -1

        """

        for counter in range(max_request_count):
            if [overview for overview in self.get()
                    if overview.id == device_id
                    and overview.status == value]:
                return counter
            time.sleep(1)
        return -1
