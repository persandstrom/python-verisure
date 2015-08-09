""" Command line interface for Verisure MyPages """

from __future__ import print_function
import argparse
from mypages import MyPages
from mypages import (
    SMARTPLUG_ON, SMARTPLUG_OFF,
    ALARM_STATUS_ARMED_HOME, ALARM_STATUS_ARMED_AWAY, ALARM_STATUS_DISARMED
    )

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
        'get',
        help='Read status of one or many device types')
    get_parser.add_argument(
        'devices',
        nargs='+',
        choices=['alarm', 'climate', 'smartplug', 'ethernet'],
        help='Read status for device type',
        default=[])

    # Set command
    set_parser = commandsparser.add_parser(
        'set',
        help='Set status of a device')
    set_device = set_parser.add_subparsers(
        help='device',
        dest='device')

    # Set smartplug
    set_smartplug = set_device.add_parser(
        'smartplug',
        help='set smartplug value')
    set_smartplug.add_argument(
        'serial_number',
        help='serial number')
    set_smartplug.add_argument(
        'new_value',
        choices=[
            SMARTPLUG_ON,
            SMARTPLUG_OFF],
        help='new value')

    # Set alarm
    set_alarm = set_device.add_parser('alarm', help='set alarm status')
    set_alarm.add_argument(
        'code',
        help='alarm code')
    set_alarm.add_argument(
        'new_status',
        choices=[
            ALARM_STATUS_ARMED_HOME,
            ALARM_STATUS_ARMED_AWAY,
            ALARM_STATUS_DISARMED],
        help='new status')

    args = parser.parse_args()

    with MyPages(args.username, args.password) as verisure:
        if args.command == 'get':
            for device in args.devices:
                if device == 'alarm':
                    print(verisure.get_alarm_status())
                if device == 'climate':
                    print(verisure.get_climate_status())
                if device == 'smartplug':
                    print(verisure.get_smartplug_status())
                if device == 'ethernet':
                    print(verisure.get_ethernet_status())
        if args.command == 'set':
            if args.device == 'smartplug':
                verisure.set_smartplug_status(args.serial_number, args.new_value)
            if args.device == 'alarm':
                verisure.set_alarm_status(args.code, args.new_status)
