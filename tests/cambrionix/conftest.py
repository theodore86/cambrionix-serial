import os
import pytest
import serial_mock
from collections import OrderedDict
from cambrionix.entities.cli import CambrionixCli, StateParser
from cambrionix.entities.hub import PortFlags
from cambrionix.terminal.entities import LineBreaks


@pytest.fixture()
def ini_filepath(request):
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), request.param
        )
    )


INI = 'cbrx.ini'

HOST_A = {
    'default_enter': '\\r\\n',
    'encoding': 'utf-8',
    'port': 'DJ00JL41',
    'prompt': '>>',
    'return_response': '\\r\\n',
    'serial_speed': 'slow',
    'timeout': '10.0',
    'write_timeout': '3.0'
}
HOST_B = {
    'default_enter': '\\n',
    'encoding': 'utf-8',
    'port': 'DN00A2E6',
    'prompt': '>>',
    'return_response': '\\n',
    'serial_speed': 'fast',
    'timeout': '10.0',
    'write_timeout': '3.0'
}


def port_map(values):
    return OrderedDict(list(zip(StateParser.keys, values)))


SHOW_PORT_STATE = (
    dict(response='1, 0000, D O, 0, 0, x, 0.00'),
    ('1', port_map(['0000', PortFlags('O', 'D'), '0', '0', 'x', '0.00']))
)


SHOW_PORTS_STATE = (
    dict(response='1: 0946: R A S: 1: 0: x: 0.10\n2: 0540: A S: 2: 60: 120: 0.15',
         newline='\n',
         linesep=':'
         ),
    [
        ('1', port_map(['0946', PortFlags('S', 'A', 'R'), '1', '0', 'x', '0.10'])),
        ('2', port_map(['0540', PortFlags('S', 'A'), '2', '60', '120', '0.15']))
    ]
)


@pytest.fixture(scope='session')
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope='session')
def dummy_serial():
    def create_dummy_serial(test_class):
        return serial_mock.DummySerial(test_class)
    return create_dummy_serial


class MockCbrxSerialCli(serial_mock.MockSerial):
    port = '/dev/cu.usbserial-DO02XXX'
    prompt = '>>>'
    serial_speed = 'slow'
    delimiter = str(LineBreaks.CRLF)
    endline = str(LineBreaks.CRLF)

    @classmethod
    def _command_echo(cls, command, *args):
        command = command + ' '.join(args)
        command += cls.delimiter
        return command

    @serial_mock.serial_query('state')
    def state(self, port=''):
        command = self.__class__._command_echo('state', port)
        response = '{}, 0946, A S, 1, 0, x, 0.10'.format(port)
        return ''.join([command, response])

    @serial_mock.serial_query('mode')
    def mode(self, mode, port=''):
        command = self.__class__._command_echo('mode', mode, port)
        return command

    @serial_mock.serial_query('system')
    def system(self):
        command = self.__class__._command_echo('system')
        response = 'cambrionix PP15S 15 Port USB Charge+Sync'
        return ''.join([command, response])


@pytest.fixture(scope='session')
def cli(dummy_serial, monkeysession):
    monkeysession.setattr(
        CambrionixCli, '_is_valid_port', lambda inst, port: (True, port)
    )
    cli = CambrionixCli(
        MockCbrxSerialCli.port,
        serial_speed=MockCbrxSerialCli.serial_speed,
        prompt=MockCbrxSerialCli.prompt,
        default_enter=MockCbrxSerialCli.delimiter,
        response_return=MockCbrxSerialCli.endline
    )
    monkeysession.setattr(
        cli._conn, '_conn', dummy_serial(MockCbrxSerialCli)  # mock pyserial
    )
    yield cli
    cli.stop()
