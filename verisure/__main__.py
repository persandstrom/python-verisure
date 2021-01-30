""" Command line interface for Verisure MyPages """

import click
import inspect
import json
import re
from verisure import VariableTypes, Session, ResponseError


class DeviceLabel(click.ParamType):
    name = "DeviceLabel"

    def convert(self, value, param, ctx):
        if re.match(r"^([A-Z]|[0-9]){4} ([A-Z]|[0-9]){4}$", value):
            return value
        self.fail(f"{value!r} is not a a device label", param, ctx)


class ArmFutureState(click.ParamType):
    name = "FutureState"


class LockFutureState(click.ParamType):
    name = "FutureState"


class TransactionId(click.ParamType):
    name = "TransactionId"


class Code(click.ParamType):
    name = "Code"


VariableTypeMap = {
    VariableTypes.DeviceLabel: DeviceLabel(),
    VariableTypes.ArmFutureState: ArmFutureState(),
    VariableTypes.LockFutureState: LockFutureState(),
    bool: click.BOOL,
    VariableTypes.TransactionId: TransactionId(),
    VariableTypes.Code: Code(),
}


def options_from_operator_list():
    def decorator(f):
        ops = inspect.getmembers(Session, predicate=inspect.isfunction)
        for name, operation in reversed(ops):
            if not hasattr(operation, 'is_query'):
                continue
            variables = list(operation.__annotations__.values())
            dashed_name = name.replace('_', '-')
            if len(variables) == 0:
                click.option(
                    '--'+dashed_name,
                    is_flag=True,
                    help=operation.__doc__)(f)
            elif len(variables) == 1:
                click.option(
                    '--'+dashed_name,
                    type=VariableTypeMap[variables[0]],
                    help=operation.__doc__)(f)
            else:
                types = [VariableTypeMap[variable] for variable in variables]
                click.option(
                    '--'+dashed_name,
                    type=click.Tuple(types),
                    help=operation.__doc__)(f)
        return f
    return decorator


def make_query(session, name, arguments):
    if(arguments is True):
        return getattr(session, name)()
    if(type(arguments) is str):
        return getattr(session, name)(arguments)
    return getattr(session, name)(*arguments)


@click.command()
@click.argument('username')
@click.argument('password')
@click.option('-i', '--installation', 'installation', help='Installation number', type=int, default=1)  # noqa: E501
@click.option('-c', '--cookie', 'cookie', help='File to store cookie in', default='~/.verisure-cookie')  # noqa: E501
@options_from_operator_list()
def cli(username, password, installation, cookie, *args, **kwargs):
    """Read and change status of verisure devices through verisure app API"""
    try:
        session = Session(username, password, cookie)
        installations = session.login()
        session.set_giid(
            installations['data']['account']
            ['installations'][installation]['giid'])
        queries = [
            make_query(session, name, arguments)
            for name, arguments in kwargs.items()
            if arguments]
        result = session.request(*queries)
        click.echo(json.dumps(result, indent=4, separators=(',', ': ')))

    except ResponseError as ex:
        print(ex.text)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
