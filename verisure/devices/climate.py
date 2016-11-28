"""
Climate device
"""

OVERVIEW_URL = '/overview/climatedevice'
DATA_URL = '/start/getclimatedata.cmd'


class Climate(object):
    """ Climate device

    Args:
        session (verisure.session): Current session
    """
    def __init__(self, session):
        self._session = session

    def get_history(self, *serial_numbers):
        """ get historical climate data

        Args:
            *serial_numbers: Devices to request history for
        """

        data = {
            'deviceLabels[]': serial_numbers
        }
        return self._session.post(DATA_URL, data)
