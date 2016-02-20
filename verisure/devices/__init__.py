""" submodule containing supported devices """

__all__ = [
    'Alarm',
    'Climate',
    'Ethernet',
    'Lock',
    'Mousedetection',
    'Smartcam',
    'Smartplug',
    'Temperaturecontrol',
    'Vacationmode',
]

from .alarm import Alarm
from .climate import Climate
from .ethernet import Ethernet
from .lock import Lock
from .mousedetection import Mousedetection
from .smartcam import Smartcam
from .smartplug import Smartplug
from .temperaturecontrol import Temperaturecontrol
from .vacationmode import Vacationmode
