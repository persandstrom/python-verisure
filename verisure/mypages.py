"""
API to communicate with Verisure mypages
"""

import verisure.devices as devices

from verisure.session import Session


class MyPages(object):
    """ Interface to verisure MyPages

    Args:
        username (str): Username used to log in to mypages
        password (str): Password used to log in to mypages
        installation (int): Installation number
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, username, password, installation=1):
        self._session = Session(username, password, installation)

        self.alarm = devices.Alarm(self._session)
        self.climate = devices.Climate(self._session)
        self.ethernet = devices.Ethernet(self._session)
        self.eventlog = devices.Eventlog(self._session)
        self.lock = devices.Lock(self._session)
        self.mousedetection = devices.Mousedetection(self._session)
        self.nest = devices.Nest(self._session)
        self.smartcam = devices.Smartcam(self._session)
        self.smartplug = devices.Smartplug(self._session)
        self.temperaturecontrol = devices.Temperaturecontrol(self._session)
        self.vacationmode = devices.Vacationmode(self._session)

    def __enter__(self):
        """ Enter context manager, open session """
        self.login()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """ Exit context manager, close session """
        self.logout()

    def login(self):
        """ Login to mypages

        Login before calling any read or write commands

        """
        self._session.login()

    def get_overviews(self):
        """ Get overviews from all devices """
        overviews = []
        overviews.extend(self.alarm.get())
        overviews.extend(self.climate.get())
        overviews.extend(self.ethernet.get())
        overviews.extend(self.temperaturecontrol.get())
        overviews.extend(self.lock.get())
        overviews.extend(self.mousedetection.get())
        overviews.extend(self.nest.get())
        overviews.extend(self.smartcam.get())
        overviews.extend(self.smartplug.get())
        overviews.extend(self.vacationmode.get())
        return overviews

    def logout(self):
        """ Ends session

        note:
            Ends the session, will not call the logout command on mypages

        """
        self._session.logout()
