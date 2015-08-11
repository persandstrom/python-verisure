"""
A python module for reading and changing status of verisure devices through
mypages.
"""

__all__ = [
    'MyPages',
    'get_overviews',
    'SMARTPLUG_ON',
    'SMARTPLUG_OFF',
    'ALARM_ARMED_HOME',
    'ALARM_ARMED_AWAY',
    'ALARM_DISARMED'
    ]

from .mypages import (
    MyPages,
    get_overviews,
    SMARTPLUG_ON,
    SMARTPLUG_OFF,
    ALARM_ARMED_HOME,
    ALARM_ARMED_AWAY,
    ALARM_DISARMED
    )
