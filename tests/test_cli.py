"""Tests for the verisure CLI option parsing.

Three option patterns are generated from Session query methods:
  - Flag: no arguments (e.g. --arm-state)
  - Required+optional args via QueryOption (e.g. --arm-away CODE [FORCE_ARM])
  - No options passed at all
"""

from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from verisure.__main__ import cli


def invoke(*args):
    runner = CliRunner()
    return runner.invoke(cli, ['user@example.com', 'password'] + list(args))


def test_help_shows_all_option_patterns():
    """--help should render all four option patterns correctly.

    Patterns:
      - Flag (no metavar):                --arm-state
      - Single required arg:              --disarm CODE
      - Multiple required args (tuple):   --door-lock <DEVICELABEL CODE>...
      - Required+optional (QueryOption):  --arm-away CODE [FORCE_ARM=False]
      - Optional-only (QueryOption):      --cameras-image-series [LIMIT=50] [OFFSET=0]
    """
    runner = CliRunner(env={'COLUMNS': '120'})
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert '--arm-state ' in result.output                                  # flag: no metavar
    assert '--disarm CODE' in result.output                                 # single required arg
    assert '--door-lock <DEVICELABEL CODE>' in result.output                # tuple of required args
    assert '--arm-away CODE [FORCE_ARM=False]' in result.output             # required + optional
    assert '--cameras-image-series [LIMIT=50] [OFFSET=0]' in result.output  # optional only


@patch('verisure.__main__.Session')
def test_no_options_outputs_empty_result(MockSession):
    """Pattern: no query options — should succeed and print an empty result."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}
    session.request.return_value = []
    MockSession.return_value = session

    result = invoke()
    assert result.exit_code == 0
    assert result.output.strip() == '[]'


@patch('verisure.__main__.Session')
def test_required_and_optional_args_pattern_with_required_arg(MockSession):
    """Pattern: QueryOption with required+optional args — required arg provided should succeed."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}

    session.request.return_value = []
    MockSession.return_value = session

    result = invoke('--arm-away', '1234')
    assert result.exit_code == 0


def test_required_and_optional_args_pattern_missing_required_arg():
    """Pattern: QueryOption with required+optional args — missing required arg should fail."""
    runner = CliRunner()
    result = runner.invoke(cli, ['user@example.com', 'password', '--arm-away'])
    assert result.exit_code != 0
    assert '--arm-away' in result.output


@patch('verisure.__main__.Session')
def test_flag_pattern(MockSession):
    """Pattern: flag option with no arguments — should succeed without any argument."""
    session = MagicMock()
    session.login_cookie.return_value = {
        'data': {'account': {'installations': [{'giid': 'abc'}]}}}
    session.request.return_value = []
    MockSession.return_value = session

    result = invoke('--arm-state')
    assert result.exit_code == 0
