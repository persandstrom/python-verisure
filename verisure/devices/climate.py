"""
Climate device
"""

from .overview import Overview

OVERVIEW_URL = '/overview/climatedevice'
DATA_URL = '/start/getclimatedata.cmd'


class Climate(object):
    """ Climate device

    Args:
        session (verisure.session): Current session
    """
    def __init__(self, session):
        self._session = session

    def get(self):
        """ get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('climate', val) for val in status]

    def get_history(self, *serial_numbers):
        """ get historical climate data

        Args:
            *serial_numbers: Devices to request history for
        """

        data = {
            'deviceLabels[]': serial_numbers
        }
        return self._session.post(DATA_URL, data)
