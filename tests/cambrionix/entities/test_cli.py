""" Unit tests Cambrionix command line interface """

import pytest
from contextlib import contextmanager
from cambrionix.entities.cli import CliValidator, StateParser, TerminalCommands
from cambrionix.exceptions import GenericError, FatalError
from ..conftest import SHOW_PORT_STATE, SHOW_PORTS_STATE


@contextmanager
def does_not_raise():
    yield


@pytest.fixture
def validator():
    return CliValidator


@pytest.mark.parametrize('response, expectation', [
    (r'*E410: Port number must be 1..8', pytest.raises(GenericError)),
    (r'*E410:  Port number must be 1..8', pytest.raises(GenericError)),
    (r'*E421: Invalid mode. Expected: c (charge), s (sync), b (biassed), or o (off)', pytest.raises(GenericError)),
    ('E900: Invalid bootloader command', does_not_raise()),
    ('EEror: Invalid command parameter', does_not_raise()),
    (r'*E44: Cambrionix PP15S 15 Port USB Charge+Sync', does_not_raise()),
    (r'*FATAL ERROR E001: Error text', pytest.raises(FatalError)),
    (r'*FATAL EE001: Error text', pytest.raises(FatalError))
])
def test_cli_validator(validator, response, expectation):
    with expectation:
        validator.validate(response)


@pytest.fixture
def state_parser(request):
    return StateParser(**request.param)


@pytest.mark.parametrize(
    'state_parser, expected',
    [SHOW_PORT_STATE],
    indirect=['state_parser']
)
def test_show_port_state_response_parser(state_parser, expected):
    assert next(state_parser.process()) == expected


@pytest.mark.parametrize(
    'state_parser, expected',
    [SHOW_PORTS_STATE],
    indirect=['state_parser']
)
def test_show_ports_state_response_parser(state_parser, expected):
    actual = state_parser.process()
    for a, e in zip(actual, expected):
        assert a == e


@pytest.mark.parametrize('attributes, expectation', [
    (dict(response=list()), pytest.raises(ValueError)),
    (dict(response='1,0946,A S,1,0,x,0.10', newline='\r\r'), pytest.raises(ValueError)),
    (dict(response=''), pytest.raises(ValueError, match=r'Row format.*')),
    (dict(response='2, 0946, A S, 1'), pytest.raises(ValueError, match=r'Row format.*'))
])
def test_show_state_response_parse_errors(attributes, expectation):
    with expectation:
        p = StateParser(**attributes)
        next(p.process())


@pytest.mark.parametrize('command, args, expected', [
    ('state', (None,), 'state'),
    ('state', (1,), 'state 1'),
    ('reboot', (False,), 'reboot'),
    ('reboot', (True,), 'reboot watchdog'),
    ('mode', ('OFF',), 'mode o'),
    ('mode', ('SYNC', 1), 'mode s 1'),
    ('mode', ('S', 2), 'mode s 2')
])
def test_terminal_commands(command, args, expected):
    assert getattr(TerminalCommands, command)(*args) == expected


@pytest.mark.parametrize('command, expected', [
    ('state 2', '2, 0946, A S, 1, 0, x, 0.10'),
    ('mode s 3', ''),
    ('system', 'cambrionix PP15S 15 Port USB Charge+Sync')
])
def test_cbrx_cli(cli, command, expected):
    response = cli.send_command(command)
    assert response == expected


@pytest.mark.parametrize('speed, expectation', [
    ('slow', does_not_raise()),
    ('fast', does_not_raise()),
    ('115200', pytest.raises(ValueError)),
    (57600, pytest.raises(ValueError)),
    (None, pytest.raises(ValueError)),
    (list(), pytest.raises(ValueError)),
])
def test_cbrx_cli_serial_speed(cli, speed, expectation):
    with expectation:
        cli.serial_speed = speed
