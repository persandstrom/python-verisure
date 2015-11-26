"""
A python module for reading and changing status of verisure devices through
mypages.
"""

__all__ = [
    'Error',
    'LoginError',
    'ResponseError',
    'MyPages',
    ]

from .mypages import MyPages
from .session import (
    Error,
    LoginError,
    ResponseError)


ALARM_ARMED_HOME = 'ARMED_HOME'
ALARM_ARMED_AWAY = 'ARMED_AWAY'
ALARM_DISARMED = 'DISARMED'
LOCK_LOCKED = 'LOCKED'
LOCK_UNLOCKED = 'UNLOCKED'
SMARTPLUG_ON = 'on'
SMARTPLUG_OFF = 'off'
