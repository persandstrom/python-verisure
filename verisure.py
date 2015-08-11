""" Command line interface for Verisure MyPages """

from __future__ import print_function
import argparse

from verisure import MyPages
from verisure import Alarm, Climate, Ethernet, Smartplug

COMMAND_GET = 'get'
COMMAND_SET = 'set'

DEVICE_ALARM = Alarm.__name__.lower()
DEVICE_SMARTPLUG = Smartplug.__name__.lower()
DEVICE_ETHERNET = Ethernet.__name__.lower()
DEVICE_CLIMATE = Climate.__name__.lower()


def print_status(status):
    ''' print the status of a device '''
    for device in status:
        print(device.__class__.__name__)
        for key, value in device.__dict__.items():
            print('\t{}: {}'.format(key, value))

# pylint: disable=C0103
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Read or change status of verisure devices')
    parser.add_argument(
        'username',
        help='MySite username')
    parser.add_argument(
        'password',
        help='MySite password')

    commandsparser = parser.add_subparsers(
        help='commands',
        dest='command')

    # Get command
    get_parser = commandsparser.add_parser(
        COMMAND_GET,
        help='Read status of one or many device types')
    get_parser.add_argument(
        'devices',
        nargs='+',
        choices=[
            DEVICE_ALARM,
            DEVICE_CLIMATE,
            DEVICE_SMARTPLUG,
            DEVICE_ETHERNET
            ],
        help='Read status for device type',
        default=[])

    # Set command
    set_parser = commandsparser.add_parser(
        COMMAND_SET,
        help='Set status of a device')
    set_device = set_parser.add_subparsers(
        help='device',
        dest='device')

    # Set smartplug
    set_smartplug = set_device.add_parser(
        DEVICE_SMARTPLUG,
        help='set smartplug value')
    set_smartplug.add_argument(
        'serial_number',
        help='serial number')
    set_smartplug.add_argument(
        'new_value',
        choices=[
            Smartplug.STATE_ON,
            Smartplug.STATE_OFF],
        help='new value')

    # Set alarm
    set_alarm = set_device.add_parser(
        DEVICE_ALARM,
        help='set alarm status')
    set_alarm.add_argument(
        'code',
        help='alarm code')
    set_alarm.add_argument(
        'new_status',
        choices=[
            Alarm.STATE_ARMED_HOME,
            Alarm.STATE_ARMED_AWAY,
            Alarm.STATE_DISARMED],
        help='new status')

    args = parser.parse_args()

    with MyPages(args.username, args.password) as verisure:
        if args.command == COMMAND_GET:
            for dev in args.devices:
                if dev == DEVICE_ALARM:
                    print_status(verisure.get_alarm_status())
                if dev == DEVICE_CLIMATE:
                    print_status(verisure.get_climate_status())
                if dev == DEVICE_SMARTPLUG:
                    print_status(verisure.get_smartplug_status())
                if dev == DEVICE_ETHERNET:
                    print_status(verisure.get_ethernet_status())
        if args.command == COMMAND_SET:
            if args.device == DEVICE_SMARTPLUG:
                verisure.set_smartplug_status(
                    args.serial_number,
                    args.new_value)
            if args.device == DEVICE_ALARM:
                verisure.set_alarm_status(
                    args.code,
                    args.new_status)
