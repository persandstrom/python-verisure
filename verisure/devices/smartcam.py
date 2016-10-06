"""
Smartcam device
"""


from .overview import Overview

OVERVIEW_URL = '/overview/camera'
CAPTURE_URL = '/picturelog/camera/{}/capture.cmd'


class Smartcam(object):
    """ Smartcam device

    Args:
        session (verisure.session): Current session
    """

    def __init__(self, session):
        self._session = session

    def get(self):
        """ Get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('smartcam', val) for val in status]

    def capture(self, device_id):
        """Capture a new image to mypages

            Args:
                device_id (str): smartcam device id
        """
        data = {}
        return not self._session.post((CAPTURE_URL.format(
            device_id.upper().replace(' ', '%20'))), data)
