"""
Temperaturecontrol device
"""

from .overview import Overview

OVERVIEW_URL = '/overview/temperaturecontrol'


class Temperaturecontrol(object):
    """ Temperaturecontrol device

    Args:
        session (verisure.session): Current session
    """
    def __init__(self, session):
        self._session = session

    def get(self):
        """ Get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('temperaturecontrol', val) for val in status]
