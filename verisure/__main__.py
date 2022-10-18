""" Command line interface for Verisure MyPages """

import inspect
import json
import re
import click
from verisure import VariableTypes, Session, ResponseError, LoginError


class DeviceLabel(click.ParamType):
    """Click param for device label"""
    name = "DeviceLabel"

    def convert(self, value, param, ctx):
        if re.match(r"^([A-Z]|[0-9]){4} ([A-Z]|[0-9]){4}$", value):
            return value
        self.fail(f"{value!r} is not a device label", param, ctx)


class ArmFutureState(click.ParamType):
    """Click param for arm future state"""
    name = "FutureState"


class LockFutureState(click.ParamType):
    """Click param for lock future state"""
    name = "FutureState"


class TransactionId(click.ParamType):
    """Click param for transaction id"""
    name = "TransactionId"


class RequestId(click.ParamType):
    """Click param for request id"""
    name = "RequestId"


class Code(click.ParamType):
    """Click param for code"""
    name = "Code"

    def convert(self, value, param, ctx):
        if re.match(r"^[0-9]{4,6}$", value):
            return value
        self.fail(f"{value!r} is not a code", param, ctx)


VariableTypeMap = {
    VariableTypes.DeviceLabel: DeviceLabel(),
    VariableTypes.ArmFutureState: ArmFutureState(),
    VariableTypes.LockFutureState: LockFutureState(),
    bool: click.BOOL,
    VariableTypes.TransactionId: TransactionId(),
    VariableTypes.RequestId: RequestId(),
    VariableTypes.Code: Code(),
}


def options_from_operator_list():
    """Get all query operations and build query cli"""
    def decorator(f):
        ops = inspect.getmembers(Session, predicate=inspect.isfunction)
        for name, operation in reversed(ops):
            if not hasattr(operation, 'is_query'):
                continue
            variables = list(operation.__annotations__.values())
            # Remove Giid type from variables, not supported by CLI
            if VariableTypes.Giid in variables:
                variables.remove(VariableTypes.Giid)
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
    """make query operation"""
    if arguments is True:
        return getattr(session, name)()
    if isinstance(arguments, str):
        return getattr(session, name)(arguments)
    return getattr(session, name)(*arguments)


@click.command()
@click.argument('username')
@click.argument('password')
@click.option('-i', '--installation', 'installation', help='Installation number', type=int, default=0)  # noqa: E501
@click.option('-c', '--cookie', 'cookie', help='File to store cookie in', default='~/.verisure-cookie')  # noqa: E501
@click.option('--mfa', 'mfa', help='Login using MFA', default=False, is_flag=True)  # noqa: E501
@options_from_operator_list()
def cli(username, password, installation, cookie, mfa, **kwargs):
    """Read and change status of verisure devices through verisure app API"""

    session = Session(username, password, cookie)

    try:
        # try using the cookie first
        installations = session.login_cookie()
    except LoginError:
        installations = None

    try:
        if mfa and not installations:
            session.request_mfa()
            code = input("Enter verification code: ")
            session.validate_mfa(code)
            installations = session.login_cookie()
        elif not installations:
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
        click.echo(ex,err=True)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
