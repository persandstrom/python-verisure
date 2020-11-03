""" Command line interface for Verisure MyPages """

import click
import json
from verisure import OPERATIONS, Session


class DeviceLabel(click.ParamType):
    name = "DeviceLabel"
DEVICE_LABEL = DeviceLabel()

def options_from_operator_list():
    def decorator(f):
        for name, operation in OPERATIONS.items():
            variables = [(key, value) for key, value in operation['variables'].items() if not value]
            if(len(variables)):
                click.option(
                    '--'+name, 
                    nargs=len(variables),
                    type=DEVICE_LABEL,
                    help=operation['help'])(f)
            else:
                click.option(
                    '--'+name, 
                    is_flag=True,
                    help=operation['help'])(f)
        return f
    return decorator


@click.command()
@click.argument('username')
@click.argument('password')
@click.option('-i', '--installation', 'installation', help='Installation number', type=int, default=1)
@click.option('-c', '--cookie', 'cookie', help='File to store cookie in', default='~/.verisure-cookie')
@options_from_operator_list()
def cli(username, password, installation, cookie, *args, **kwargs):
    """Read and change status of verisure devices through verisure app API"""
    try:
        session = Session(username, password, cookie)
        installations = session.login()
        session.set_giid(installations['data']['account']['installations'][0]['giid'])
        queries = [
            session.query(
                operation,
                **dict(zip(
                    [key for key, value in operation['variables'].items() if not value],
                    [kwargs.get(name)]))
            
            ) 
            for name, operation 
            in OPERATIONS.items() 
            if kwargs.get(name)]
        result = session.request(*queries)
        click.echo(json.dumps(result, indent=4, separators=(',', ': ')))
        
    except session.ResponseError as ex:
        print(ex.text)