""" submodule containing supported devices """

__all__ = [
    'Alarm',
    'Climate',
    'Ethernet',
    'Eventlog',
    'Lock',
    'Mousedetection',
    'Nest',
    'Smartcam',
    'Smartplug',
    'Temperaturecontrol',
    'Vacationmode',
]

from .alarm import Alarm
from .climate import Climate
from .eventlog import Eventlog
from .lock import Lock
from .smartcam import Smartcam
from .smartplug import Smartplug
