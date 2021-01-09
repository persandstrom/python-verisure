""" Command line interface for Verisure MyPages """

import click
import json
from verisure import OPERATIONS, VariableTypes, Session, ResponseError


class DeviceLabel(click.ParamType):
    name = "DeviceLabel"


class FutureState(click.ParamType):
    name = "FutureState"


class TransactionId(click.ParamType):
    name = "TransactionId"


VariableTypeMap = {
    VariableTypes.DeviceLabel: DeviceLabel(),
    VariableTypes.FutureState: FutureState(),
    VariableTypes.SmartPlugState: click.BOOL,
    VariableTypes.TransactionId: TransactionId(),
}

def options_from_operator_list():
    def decorator(f):
        for name, operation in OPERATIONS.items():
            variables = [(key, value) for key, value in operation['variables'].items()]
            if len(variables) == 0:
                click.option(
                    '--'+name, 
                    is_flag=True,
                    help=operation['help'])(f)
            elif len(variables) == 1:
                click.option(
                    '--'+name, 
                    type=VariableTypeMap[variables[0][1]],
                    help=operation['help'])(f)
            else:
                types = [VariableTypeMap[variable[1]] for variable in variables]
                click.option(
                    '--'+name, 
                    type=click.Tuple(types))(f)
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
        session.set_giid(installations['data']['account']['installations'][installation]['giid'])
        
        queries = [
            session.query(
                operation,
                **dict(zip(
                    [key for key, value in operation['variables'].items()],
                    kwargs.get(name) if hasattr(kwargs.get(name), '__iter__') else [kwargs.get(name)]))
            ) 
            for name, operation 
            in OPERATIONS.items() if kwargs.get(name.replace('-', '_'))]
        result = session.request(*queries)
        click.echo(json.dumps(result, indent=4, separators=(',', ': ')))
        
    except ResponseError as ex:
        print(ex.text)

if __name__ == "__main__":
    cli()