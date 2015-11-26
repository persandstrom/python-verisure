from .overview import Overview

OVERVIEW_URL = '/overview/smartplug'
COMMAND_URL = '/smartplugs/onoffplug.cmd'


class Smartplug(object):

    SMARTPLUG_ON = 'on'
    SMARTPLUG_OFF = 'off'

    def __init__(self, session):
        self._session = session

    def get(self):
        status = self._session.get(OVERVIEW_URL)
        return [Overview('smartplug', val) for val in status]

    def set(self, device_id, value):
        data = {
            'targetDeviceLabel': device_id,
            'targetOn': value
            }
        return not self._session.post(COMMAND_URL, data)
