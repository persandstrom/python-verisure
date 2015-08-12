""" Command line interface for Verisure MyPages """

from __future__ import print_function
import argparse

from verisure import *

COMMAND_GET = 'get'
COMMAND_SET = 'set'


def print_overviews(overviews):
    ''' print the status of a device '''
    if isinstance(overviews, list):
        for overview in overviews:
            print_overview(overview)
    else:
        print_overview(overviews)

def print_overview(overview):
    print(overview.get_typename())
    for key, value in overview.get_status():
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
        choices=get_overviews(),
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
    set_alarm = set_device.add_parser(
        'alarm',
        help='set alarm status')
    set_alarm.add_argument(
        'code',
        help='alarm code')
    set_alarm.add_argument(
        'new_status',
        choices=[
            ALARM_ARMED_HOME,
            ALARM_ARMED_AWAY,
            ALARM_DISARMED],
        help='new status')

    args = parser.parse_args()

    with MyPages(args.username, args.password) as verisure:
        if args.command == COMMAND_GET:
            for dev in args.devices:
                print_overviews(verisure.get_overview(dev))
        if args.command == COMMAND_SET:
            if args.device == 'smartplug':
                verisure.set_smartplug_status(
                    args.serial_number,
                    args.new_value)
            if args.device == 'alarm':
                verisure.set_alarm_status(
                    args.code,
                    args.new_status)
