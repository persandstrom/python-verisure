from .overview import Overview

OVERVIEW_URL = '/overview/vacationmode'

class Vacationmode(object):

    def __init__(self, session):
        self._session = session

    def get(self):
        status = self._session.get(OVERVIEW_URL)
        return [Overview('vacationmode', status)]
