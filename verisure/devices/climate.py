"""
Climate device
"""

from .overview import Overview

OVERVIEW_URL = '/overview/climatedevice'


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
