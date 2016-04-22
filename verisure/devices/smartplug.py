"""
Smartplug device
"""
import time

from .overview import Overview

OVERVIEW_URL = '/settings/smartplug'
COMMAND_URL = '/smartplugs/onoffplug.cmd'
DETAILS_URL = '/smarthome/{}/details'


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

    def get_details(self, device_id):
        """ Get details from a smartplug

        Args:
            device_id (str): Id of the smartplug
        """
        return self._session.get(DETAILS_URL.format(
            device_id.upper().replace(' ', '%20')))

    def set_location(self, device_id, location):
        """ Set smartplug location

        Args:
            device_id (str): Id of the smartplug
            location (str): New location
        """
        details_url = DETAILS_URL.format(
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
                    if overview.deviceLabel == device_id and
                    overview.status == value]:
                return counter
            time.sleep(1)
        return -1
