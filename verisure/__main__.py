""" Command line interface for Verisure MyPages """

from __future__ import print_function
import click
import json
import verisure
from .operations import OPERATIONS

COMMAND_USER_TRACKINGS = 'user_trackings' 


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
@click.command()
def main():
    """Verisure ..."""
    click.echo("")
    args = None
#    """ Start verisure command line """
#    parser = argparse.ArgumentParser(
#        description='Read or change status of verisure devices')
#    parser.add_argument(
#        'username',
#        help='MyPages username')
#    parser.add_argument(
#        'password',
#        help='MyPages password')
#    parser.add_argument(
#        '-i', '--installation',
#        help='Installation number',
#        type=int,
#        default=1)
#    parser.add_argument(
#        '-c', '--cookie',
#        help='File to store cookie in',
#        default='~/.verisure-cookie')

    
    for name, operation in OPERATIONS.items():
        group = parser.add_argument_group(name)
        arguments = [key for key, value in operation["variables"].items() if value == None]
        if arguments:
            group.add_argument("--"+name)
            for argument in arguments:
                group.add_argument(argument)
        else:
            group.add_argument("--"+name, action='store_true')
            

    args = parser.parse_args()
    session = verisure.Session(args.username, args.password, args.cookie)
    print(args)
#    installations = session.login()
    try:
 #       session.set_giid(installations['data']['account']['installations'][0]['giid'])

        if args.command in OPERATIONS:

            print_result(session.request(session.query(
                OPERATIONS[args.command],
                )))
    except verisure.session.ResponseError as ex:
        print(ex.text)


# pylint: disable=C0103
if __name__ == "__main__":
    main()
