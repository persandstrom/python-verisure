"""Tests for the verisure CLI option parsing."""

from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from verisure.__main__ import cli


def invoke(*args):
    runner = CliRunner()
    return runner.invoke(cli, ['user@example.com', 'password'] + list(args))


@patch('verisure.__main__.Session')
def test_no_query_options(MockSession):
    """Invoking without arm-away/arm-home must not raise an arity error."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}
    session.request.return_value = []
    MockSession.return_value = session

    result = invoke('--arm-state')
    assert 'requires at least 1 argument' not in (result.output + str(result.exception))


@patch('verisure.__main__.Session')
def test_arm_away_with_code(MockSession):
    """--arm-away with a valid code should be accepted."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}
    session.request.return_value = []
    MockSession.return_value = session

    result = invoke('--arm-away', '1234')
    assert result.exit_code == 0


def test_arm_away_missing_code():
    """--arm-away without a code should fail with a usage error."""
    runner = CliRunner()
    # Pass --arm-away as the last argument so there is no code after it
    result = runner.invoke(cli, ['user@example.com', 'password', '--arm-away'])
    assert result.exit_code != 0
    assert 'requires at least 1 argument' in (result.output + str(result.exception))


@patch('verisure.__main__.Session')
def test_arm_home_with_code(MockSession):
    """--arm-home with a valid code should be accepted."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}
    session.request.return_value = []
    MockSession.return_value = session

    result = invoke('--arm-home', '1234')
    assert result.exit_code == 0


@patch('verisure.__main__.Session')
def test_flag_option(MockSession):
    """A plain flag option like --arm-state should work without arguments."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}
    session.request.return_value = []
    MockSession.return_value = session

    result = invoke('--arm-state')
    assert result.exit_code == 0
