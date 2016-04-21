""" Command line interface for Verisure MyPages """

from __future__ import print_function

import argparse
import pprint

from verisure import MyPages

COMMAND_GET = 'get'
COMMAND_SET = 'set'
COMMAND_HISTORY = 'history'


def print_overviews(overviews):
    ''' print the overviews of devices '''
    if isinstance(overviews, list):
        for overview in overviews:
            print_overview(overview)
    else:
        print_overview(overviews)


def print_overview(overview):
    """ print the overview of a device """
    print(overview.get_typename())
    for key, value in overview.get_status():
        print(u'\t{}: {}'.format(key, value))


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
        nargs='*',
        choices=[
            'alarm',
            'climate',
            'ethernet',
            'lock',
            'mousedetection',
            'nest',
            'smartcam',
            'smartplug',
            'temperaturecontrol',
            'vacationmode',
            'all'
        ],
        help='Read status for device type')

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
            'on',
            'off'],
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
            'ARMED_HOME',
            'ARMED_AWAY',
            'DISARMED'],
        help='new status')

    # Set lock
    set_lock = set_device.add_parser(
        'lock',
        help='set lock status')
    set_lock.add_argument(
        'code',
        help='alarm code')
    set_lock.add_argument(
        'serial_number',
        help='serial number')
    set_lock.add_argument(
        'new_status',
        choices=[
            'LOCKED',
            'UNLOCKED'],
        help='new status')

    # History command
    history_parser = commandsparser.add_parser(
        COMMAND_HISTORY,
        help='Get history of a device')
    history_device = history_parser.add_subparsers(
        help='device',
        dest='device')

    # Get climate history
    history_climate = history_device.add_parser(
        'climate',
        help='get climate history')
    history_climate.add_argument(
        'serial_numbers',
        nargs='+',
        help='serial numbers')

    args = parser.parse_args()

    with MyPages(args.username, args.password) as verisure:
        if args.command == COMMAND_GET:
            if 'all' in args.devices:
                print_overviews(verisure.get_overviews())
            else:
                for dev in args.devices:
                    print_overviews(verisure.__dict__[dev].get())
        if args.command == COMMAND_SET:
            if args.device == 'smartplug':
                print(verisure.smartplug.set(
                    args.serial_number,
                    args.new_value))
            if args.device == 'alarm':
                print(verisure.alarm.set(
                    args.code,
                    args.new_status))
            if args.device == 'lock':
                print(verisure.lock.set(
                    args.code,
                    args.serial_number,
                    args.new_status))
        if args.command == COMMAND_HISTORY:
            if args.device == 'climate':
                pprint.PrettyPrinter().pprint(verisure.climate.get_history(
                    *args.serial_numbers))
