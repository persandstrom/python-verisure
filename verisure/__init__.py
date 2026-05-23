"""
A python module for reading and changing status of verisure devices through
verisure app API.
"""

__all__ = [
    'AuthenticationError',
    'CookieReadError',
    'Error',
    'LoginError',
    'RateLimitError',
    'RequestError',
    'ResponseError',
    'Session',
]

from .session import ( # NOQA
    AuthenticationError,
    CookieReadError,
    Error,
    LoginError,
    RateLimitError,
    RequestError,
    VariableTypes,
    ResponseError,
    Session,
)

ALARM_ARMED_HOME = 'ARMED_HOME'
ALARM_ARMED_AWAY = 'ARMED_AWAY'
ALARM_DISARMED = 'DISARMED'
LOCK_LOCKED = 'LOCKED'
LOCK_UNLOCKED = 'UNLOCKED'
SMARTPLUG_ON = 'on'
SMARTPLUG_OFF = 'off'
