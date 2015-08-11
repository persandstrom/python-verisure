"""
A python module for reading and changing status of verisure devices through
mypages.
"""

__all__ = ['MyPages', 'Device', 'Alarm', 'Climate', 'Ethernet', 'Smartplug']

from .mypages import MyPages
from .mypages import Device, Alarm, Climate, Ethernet, Smartplug
