""" submodule containing supported devices """

__all__ = [
    'Alarm',
    'Climate',
    'Ethernet',
    'Heatpump',
    'Lock',
    'Mousedetection',
    'Smartcam',
    'Smartplug',
    'Vacationmode',
]

from .alarm import Alarm
from .climate import Climate
from .ethernet import Ethernet
from .heatpump import Heatpump
from .lock import Lock
from .mousedetection import Mousedetection
from .smartcam import Smartcam
from .smartplug import Smartplug
from .vacationmode import Vacationmode
