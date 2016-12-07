""" Command line interface for Verisure MyPages """

from __future__ import print_function

import argparse
import pprint

from verisure import session

COMMAND_OVERVIEW = 'overview'
COMMAND_SET = 'set'
COMMAND_HISTORY = 'history'
COMMAND_EVENTLOG = 'eventlog'
COMMAND_INSTALLATIONS = 'installations'

try:
    unicode = unicode
except:
    unicode = str


def print_overview(overview, depth, *names):
    indent = '  ' * depth
    if isinstance(overview, list):
        for item in overview:
            print('{}{}:'.format(indent, item.__name__))
            print_overview(item, depth + 1)
    else:
        for key, value in overview.__dict__.items():
            if key.startswith('_') or (names and key not in names and depth==0):
                continue
            if not value:
                print('{}{}: {}'.format(indent, key, value))
            elif isinstance(value, str):
                print('{}{}: {}'.format(indent, key, value))
            elif isinstance(value, unicode):
                print('{}{}: {}'.format(indent, key, value.encode('utf8')))
            elif isinstance(value, list):
                for item in value:
                    print('{}{}:'.format(indent, key))
                    print_overview(item, depth + 1)
            else:
                print('{}{}:'.format(indent, key))
                print_overview(value, depth + 1)


def main():
    """ Start verisure command line """
    parser = argparse.ArgumentParser(
        description='Read or change status of verisure devices')
    parser.add_argument(
        'username',
        help='MySite username')
    parser.add_argument(
        'password',
        help='MySite password')
    parser.add_argument(
        '-i', '--installation',
        help='Installation number',
        type=int,
        default=1)

    commandsparser = parser.add_subparsers(
        help='commands',
        dest='command')

    # installations command
    installations_parser = commandsparser.add_parser(
        COMMAND_INSTALLATIONS,
        help='Get information about installations')

    # overview command
    overview_parser = commandsparser.add_parser(
        COMMAND_OVERVIEW,
        help='Read status of one or many device types')
    overview_parser.add_argument(
        'filter',
        nargs='*',
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
        'device_label',
        help='device label')

    # Event log command
    eventlog_parser = commandsparser.add_parser(
        COMMAND_EVENTLOG,
        help='Get event log')
    eventlog_parser.add_argument(
        '-p', '--pagesize',
        type=int,
        default=15,
        help='Number of elements on one page')
    eventlog_parser.add_argument(
        '-o', '--offset',
        type=int,
        default=0,
        help='Page offset')
    eventlog_parser.add_argument(
        '-f', '--filter',
        nargs='*',
        default=[],
        choices=[
            'ARM',
            'DISARM',
            'FIRE',
            'INTRUSION',
            'TECHNICAL',
            'SOS',
            'WARNING'],
        help='Filter event log')

    args = parser.parse_args()
    verisure = session.Session(args.username, args.password)
    verisure.login()
    verisure.set_giid(verisure.installations[args.installation - 1].giid)
    if args.command == COMMAND_INSTALLATIONS:
        print_overview(verisure.installations, 0)
    if args.command == COMMAND_OVERVIEW:
        print_overview(verisure.get_overview(), 0, *args.filter)
    if args.command == COMMAND_SET:
        if args.device == 'smartplug':
            print(verisure.set_smartplug_state(
                args.serial_number,
                args.new_value == 'on'))
        if args.device == 'alarm':
            print(verisure.set_arm_state(
                args.code,
                args.new_status))
        if args.device == 'lock':
            print(verisure.lock.set(
                args.code,
                args.serial_number,
                args.new_status))
    if args.command == COMMAND_HISTORY:
        if args.device == 'climate':
            print_overview(verisure.get_climate(args.device_label), 0)
    if args.command == COMMAND_EVENTLOG:
        print_overview(
            verisure.get_history(args.pagesize, args.offset, *args.filter), 0)


# pylint: disable=C0103
if __name__ == "__main__":
    main()
