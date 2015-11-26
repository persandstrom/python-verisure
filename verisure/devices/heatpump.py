"""
Heatpump device
"""

from .overview import Overview

OVERVIEW_URL = '/overview/heatpump'


class Heatpump(object):
    """ Heatpump device

    Args:
        session (verisure.session): Current session
    """
    def __init__(self, session):
        self._session = session

    def get(self):
        """ Get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('heatpump', val) for val in status]
