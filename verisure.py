""" Command line interface for Verisure MyPages """

from __future__ import print_function
import argparse
from mypages import MyPages

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

    subparsers = parser.add_subparsers(
        help='commands',
        dest='command')

    # Get command
    get_parser = subparsers.add_parser(
        'get',
        help='Read status of one or many device types')
    get_parser.add_argument(
        'devices',
        nargs='+',
        choices=['alarm', 'climate', 'smartplug', 'ethernet'],
        help='Read status for device type',
        default=[])

    # Set command
    set_parser = subparsers.add_parser(
        'set',
        help='Set status of a device')
    set_parser.add_argument(
        'device',
        choices=['smartplug'],
        help='Set status for device type')
    set_parser.add_argument(
        'device_id',
        help='device id')
    set_parser.add_argument(
        'new_value',
        help='new value')

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
                verisure.set_smartplug_status(args.device_id, args.new_value)
