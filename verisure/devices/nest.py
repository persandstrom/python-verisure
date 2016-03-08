"""
Nest device
"""

from .overview import Overview

OVERVIEW_URL = '/overview/nest'


class Nest(object):
    """ Nest device

    Args:
        session (verisure.session): Current session
    """
    def __init__(self, session):
        self._session = session

    def get(self):
        """ get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('nest', status)]
