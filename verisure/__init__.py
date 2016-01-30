"""
A python module for reading and changing status of verisure devices through
mypages.
"""

__all__ = [
    'Error',
    'LoggedOutError',
    'LoginError',
    'MaintenanceError',
    'MyPages',
    'ResponseError',
    'TemporarilyUnavailableError',
]

from .mypages import MyPages
from .session import (
    Error,
    LoggedOutError,
    LoginError,
    MaintenanceError,
    ResponseError,
    TemporarilyUnavailableError,
)


ALARM_ARMED_HOME = 'ARMED_HOME'
ALARM_ARMED_AWAY = 'ARMED_AWAY'
ALARM_DISARMED = 'DISARMED'
LOCK_LOCKED = 'LOCKED'
LOCK_UNLOCKED = 'UNLOCKED'
SMARTPLUG_ON = 'on'
SMARTPLUG_OFF = 'off'
