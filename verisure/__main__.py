""" Command line interface for Verisure MyPages """

import inspect
import json
import re
import click
import logging
import getpass
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
    int: click.INT,
    bool: click.BOOL,
    VariableTypes.TransactionId: TransactionId(),
    VariableTypes.RequestId: RequestId(),
    VariableTypes.Code: Code(),
}


class QueryOption(click.Option):
    """Click option that accepts required and trailing optional values."""

    def __init__(self, *args, parameter_types=None, min_arity=0, **kwargs):
        self.parameter_types = parameter_types or []
        self.min_arity = min_arity
        self.max_arity = len(self.parameter_types)
        kwargs['nargs'] = 0
        kwargs['type'] = click.UNPROCESSED
        super().__init__(*args, **kwargs)

    def add_to_parser(self, parser, ctx):
        super().add_to_parser(parser, ctx)

        def parser_process(value, state):
            values = []
            while state.rargs and len(values) < self.max_arity:
                next_arg = state.rargs[0]
                if next_arg[:1] in option_parser.prefixes:
                    break
                values.append(state.rargs.pop(0))
            state.opts[option_parser.dest] = tuple(values)
            state.order.append(self)

        option_names = self.opts + self.secondary_opts
        for option_name in option_names:
            option_parser = parser._long_opt.get(option_name) or parser._short_opt.get(option_name)
            if option_parser is None:
                continue
            option_parser.process = parser_process
            break

    def type_cast_value(self, ctx, value):
        if value is None:
            value = ()
        if not isinstance(value, tuple):
            value = (value,)

        if len(value) < self.min_arity:
            raise click.BadParameter(
                f'requires at least {self.min_arity} argument(s)')
        if len(value) > self.max_arity:
            raise click.BadParameter(
                f'accepts at most {self.max_arity} argument(s)')

        converted = []
        for raw_value, parameter_type in zip(value, self.parameter_types):
            converted.append(parameter_type.convert(raw_value, self, ctx))
        return tuple(converted)


def _get_query_parameters(operation):
    """Return CLI-relevant parameters for a query operation."""
    parameters = []
    for parameter in inspect.signature(operation).parameters.values():
        if parameter.name in ['self', 'giid']:
            continue
        parameters.append(parameter)
    return parameters


def _get_parameter_type(parameter):
    """Resolve the Click type for a Session query parameter."""
    if parameter.annotation is not inspect.Parameter.empty:
        return VariableTypeMap[parameter.annotation]
    if parameter.default is not inspect.Parameter.empty:
        return click.types.convert_type(type(parameter.default))
    return click.STRING


def _get_query_metavar(parameters):
    """Build help text for a query option's accepted argument list."""
    required_parameters = [
        parameter for parameter in parameters
        if parameter.default is inspect.Parameter.empty]
    optional_parameters = [
        parameter for parameter in parameters
        if parameter.default is not inspect.Parameter.empty]

    metavar_parts = [parameter.name.upper() for parameter in required_parameters]
    metavar_parts.extend(
        f'[{parameter.name.upper()}={parameter.default}]'
        for parameter in optional_parameters)
    return ' '.join(metavar_parts)


def options_from_operator_list():
    """Get all query operations and build query cli"""
    def decorator(f):
        ops = inspect.getmembers(Session, predicate=inspect.isfunction)
        for name, operation in reversed(ops):
            if not hasattr(operation, 'is_query'):
                continue

            parameters = _get_query_parameters(operation)
            required_parameters = [
                parameter for parameter in parameters
                if parameter.default is inspect.Parameter.empty]
            optional_parameters = [
                parameter for parameter in parameters
                if parameter.default is not inspect.Parameter.empty]
            dashed_name = name.replace('_', '-')

            if len(optional_parameters) > 0:
                parameter_types = [
                    _get_parameter_type(parameter)
                    for parameter in parameters]
                f = click.option(
                    '--' + dashed_name,
                    cls=QueryOption,
                    parameter_types=parameter_types,
                    min_arity=len(required_parameters),
                    metavar=_get_query_metavar(parameters),
                    help=operation.__doc__)(f)
            elif len(required_parameters) == 0:
                click.option(
                    '--'+dashed_name,
                    is_flag=True,
                    help=operation.__doc__)(f)
            elif len(required_parameters) == 1:
                click.option(
                    '--'+dashed_name,
                    type=_get_parameter_type(required_parameters[0]),
                    help=operation.__doc__)(f)
            else:
                types = [
                    _get_parameter_type(parameter)
                    for parameter in required_parameters]
                click.option(
                    '--'+dashed_name,
                    type=click.Tuple(types),
                    help=operation.__doc__)(f)
        return f
    return decorator


def make_query(session, name, arguments, keyword_arguments=None):
    """make query operation"""
    keyword_arguments = keyword_arguments or {}
    operation = getattr(session, name)
    parameters = _get_query_parameters(operation)

    if arguments is True:
        return operation(**keyword_arguments)

    positional_arguments = []
    if isinstance(arguments, str):
        positional_arguments = [arguments]
    elif arguments is None:
        positional_arguments = []
    else:
        positional_arguments = list(arguments)

    bound_arguments = {
        parameter.name: value
        for parameter, value in zip(parameters, positional_arguments)}
    bound_arguments.update(keyword_arguments)
    return operation(**bound_arguments)


def _collect_query_arguments(kwargs):
    """Group Click option values by query name."""
    query_arguments = {}
    for key, value in kwargs.items():
        if value in [None, False]:
            continue
        query_arguments.setdefault(key, {'arguments': None, 'keyword_arguments': {}})
        query_arguments[key]['arguments'] = value

    return query_arguments


@click.command()
@click.argument('username')
@click.argument('password', required=False)
@click.option('-i', '--installation', 'installation', help='Installation number', type=int, default=0)  # noqa: E501
@click.option('-c', '--cookie', 'cookie', help='File to store cookie in', default='~/.verisure-cookie')  # noqa: E501
@click.option('--mfa', 'mfa', help='Login using MFA', default=False, is_flag=True)  # noqa: E501
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False))  # noqa: E501
@options_from_operator_list()
def cli(username, password, installation, cookie, mfa, log_level, **kwargs):
    """
    Read and change status of verisure devices through verisure app API\n
    PASSWORD will be prompted without echoing if not provided as an argument
    """

    if not password:
        password = getpass.getpass(prompt='Password: ', stream=None)
    if log_level:
        logging.basicConfig(level=logging.getLevelName(log_level))

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

        query_arguments = _collect_query_arguments(kwargs)
        queries = [
            make_query(
                session,
                name,
                query_argument['arguments'],
                query_argument['keyword_arguments'])
            for name, query_argument in query_arguments.items()]
        result = session.request(*queries)
        click.echo(json.dumps(result, indent=4, separators=(',', ': ')))

    except ResponseError as ex:
        click.echo(ex,err=True)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
