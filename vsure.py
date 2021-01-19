""" Command line interface for Verisure MyPages """

import click
import json
import re
from verisure import OPERATIONS, VariableTypes, Session, ResponseError


class DeviceLabel(click.ParamType):
    name = "DeviceLabel"

    def convert(self, value, param, ctx):
        if re.match(r"^([A-Z]|[0-9]){4} ([A-Z]|[0-9]){4}$", value):
            return value
        self.fail(f"{value!r} is not a a device label", param, ctx)


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
        for name, operation in reversed(OPERATIONS.items()):
            variables = [(key, value) for key, value in operation['variables'].items()]
            dashed_name = name.replace('_', '-')
            if len(variables) == 0:
                click.option(
                    '--'+dashed_name,
                    is_flag=True,
                    help=operation['help'])(f)
            elif len(variables) == 1:
                click.option(
                    '--'+dashed_name,
                    type=VariableTypeMap[variables[0][1]],
                    help=operation['help'])(f)
            else:
                types = [VariableTypeMap[variable[1]] for variable in variables]
                click.option(
                    '--'+dashed_name,
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
                    [kwargs.get(name)] if len(operation['variables'].items()) < 2 else kwargs.get(name)))
            )
            for name, operation
            in OPERATIONS.items() if kwargs.get(name)]
        result = session.request(*queries)
        click.echo(json.dumps(result, indent=4, separators=(',', ': ')))

    except ResponseError as ex:
        print(ex.text)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
