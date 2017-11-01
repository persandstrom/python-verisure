""" Command line interface for Verisure MyPages """

from __future__ import print_function
import argparse
import json
import verisure

COMMAND_OVERVIEW = 'overview'
COMMAND_SET = 'set'
COMMAND_CLIMATE = 'climate'
COMMAND_EVENTLOG = 'eventlog'
COMMAND_INSTALLATIONS = 'installations'
COMMAND_CAPTURE = 'capture'
COMMAND_IMAGESERIES = 'imageseries'
COMMAND_GETIMAGE = 'getimage'
COMMAND_ARMSTATE = 'armstate'
COMMAND_DOOR_WINDOW = 'door_window'
COMMAND_VACATIONMODE = 'vacationmode'
COMMAND_TEST_ETHERNET = 'test_ethernet'


def print_result(overview, *names):
    """ Print the result of a verisure request """
    if names:
        for name in names:
            toprint = overview
            for part in name.split('/'):
                toprint = toprint[part]
            print(json.dumps(toprint, indent=4, separators=(',', ': ')))
    else:
        print(json.dumps(overview, indent=4, separators=(',', ': ')))


# pylint: disable=too-many-locals,too-many-statements
def main():
    """ Start verisure command line """
    parser = argparse.ArgumentParser(
        description='Read or change status of verisure devices')
    parser.add_argument(
        'username',
        help='MyPages username')
    parser.add_argument(
        'password',
        help='MyPages password')
    parser.add_argument(
        '-i', '--installation',
        help='Installation number',
        type=int,
        default=1)
    parser.add_argument(
        '-c', '--cookie',
        help='File to store cookie in',
        default='~/.verisure-cookie')

    commandsparser = parser.add_subparsers(
        help='commands',
        dest='command')

    # installations command
    commandsparser.add_parser(
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

    # armstate command
    commandsparser.add_parser(
        COMMAND_ARMSTATE,
        help='Get arm state')

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
        'device_label',
        help='device label')
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
            'lock',
            'unlock'],
        help='new status')

    # Get climate history
    history_climate = commandsparser.add_parser(
        COMMAND_CLIMATE,
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
            'WARNING',
            'LOCK',
            'UNLOCK'],
        help='Filter event log')

    # Capture command
    capture_parser = commandsparser.add_parser(
        COMMAND_CAPTURE,
        help='Capture image')
    capture_parser.add_argument(
        'device_label',
        help='Device label')

    # Image series command
    commandsparser.add_parser(
        COMMAND_IMAGESERIES,
        help='Get image series')

    # Get image command
    getimage_parser = commandsparser.add_parser(
        COMMAND_GETIMAGE,
        help='Download image')
    getimage_parser.add_argument(
        'device_label',
        help='Device label')
    getimage_parser.add_argument(
        'image_id',
        help='image ID')
    getimage_parser.add_argument(
        'file_name',
        help='Output file name')

    # Vacation mode command
    commandsparser.add_parser(
        COMMAND_VACATIONMODE,
        help='Get vacation mode info')

    # Door window status command
    commandsparser.add_parser(
        COMMAND_DOOR_WINDOW,
        help='Get door/window status')

    # Test ethernet command
    commandsparser.add_parser(
        COMMAND_TEST_ETHERNET,
        help='Update ethernet status')

    args = parser.parse_args()
    session = verisure.Session(args.username, args.password, args.cookie)
    session.login()
    try:
        session.set_giid(session.installations[args.installation - 1]['giid'])
        if args.command == COMMAND_INSTALLATIONS:
            print_result(session.installations)
        if args.command == COMMAND_OVERVIEW:
            print_result(session.get_overview(), *args.filter)
        if args.command == COMMAND_ARMSTATE:
            print_result(session.get_arm_state())
        if args.command == COMMAND_SET:
            if args.device == 'smartplug':
                session.set_smartplug_state(
                    args.device_label,
                    args.new_value == 'on')
            if args.device == 'alarm':
                print_result(session.set_arm_state(
                    args.code,
                    args.new_status))
            if args.device == 'lock':
                print_result(session.set_lock_state(
                    args.code,
                    args.serial_number,
                    args.new_status))
        if args.command == COMMAND_CLIMATE:
            print_result(session.get_climate(args.device_label))
        if args.command == COMMAND_EVENTLOG:
            print_result(
                session.get_history(
                    args.filter,
                    pagesize=args.pagesize,
                    offset=args.offset))
        if args.command == COMMAND_CAPTURE:
            session.capture_image(args.device_label)
        if args.command == COMMAND_IMAGESERIES:
            print_result(session.get_camera_imageseries())
        if args.command == COMMAND_GETIMAGE:
            session.download_image(
                args.device_label,
                args.image_id,
                args.file_name)
        if args.command == COMMAND_VACATIONMODE:
            print_result(session.get_vacation_mode())
        if args.command == COMMAND_DOOR_WINDOW:
            print_result(session.get_door_window())
        if args.command == COMMAND_TEST_ETHERNET:
            session.test_ethernet()
    except verisure.session.ResponseError as ex:
        print(ex.text)


# pylint: disable=C0103
if __name__ == "__main__":
    main()
