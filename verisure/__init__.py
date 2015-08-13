"""
A python module for reading and changing status of verisure devices through
mypages.
"""

__all__ = [
    'Error',
    'LoginError',
    'ResponseError',
    'MyPages'
    ]

from .mypages import (
    Error,
    LoginError,
    ResponseError,
    MyPages)
