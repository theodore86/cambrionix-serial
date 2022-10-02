""" Unit tests for serial command line interface class """

import pytest
import serial_mock
from cambrionix.terminal.cli import SerialCli
from cambrionix.terminal.entities import LineBreaks


class PyComCli(SerialCli):

    @staticmethod
    def _is_valid_port(port):
        return (True, port)

    def send_command(self, command, encoding=None):
        return self._send_command(command, encoding)


class TestCli(serial_mock.MockSerial):
    prompt = '>>>'
    baudrate = '9600'
    delimiter = str(LineBreaks.CRLF)
    endline = str(LineBreaks.CRLF)

    @serial_mock.serial_query('trigger_cmd')
    def response(self, command_echo, *response):
        command_echo += self.__class__.delimiter
        response = self.__class__.endline.join(response)
        return ''.join([command_echo, response])


@pytest.fixture(scope='session')
def cli(dummy_serial, monkeysession):
    cli = PyComCli(
        '/dev/ttyUSB0',
        baudrate=TestCli.baudrate,
        prompt=TestCli.prompt,
        default_enter=TestCli.delimiter,
        response_return=TestCli.endline
    )
    monkeysession.setattr(
        cli._conn, '_conn', dummy_serial(TestCli)
    )
    yield cli
    cli.stop()


@pytest.fixture(autouse=True)
def test_setup_teardown(cli):
    yield
    cli.prompt = TestCli.prompt
    cli.baudrate = TestCli.baudrate
    cli.response_return = TestCli.endline
    cli.default_enter = TestCli.delimiter


@pytest.mark.parametrize('value, should_raise', [
    (115200, False),
    (-10, True),
    (97000, True),
    (9600, False),
    (list(), True)
])
def test_baudrate(cli, value, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            cli.baudrate = value
    else:
        cli.baudrate = value


@pytest.mark.parametrize('value, should_raise', [
    (15, True),
    (None, True),
    ('#', False),
    (tuple(), True)
])
def test_prompt(cli, value, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            cli.prompt = value
    else:
        cli.prompt = value


@pytest.mark.parametrize('attr', ['default_enter', 'response_return'])
@pytest.mark.parametrize('value, should_raise', [
    (str(LineBreaks.LF), False),
    (str(LineBreaks.CR), False),
    (str(LineBreaks.CRLF), False),
    (r'\n\n', True),
    (r'\r\n\r', True),
    (r'\r\r', True)
])
def test_response_return_and_default_enter(cli, attr, value, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            setattr(cli, attr, value)
    else:
        setattr(cli, attr, value)


@pytest.mark.parametrize('command, expected', [
    ('trigger_cmd show_version v11.0.S444 cpm/x86_64',
     'v11.0.S444' + TestCli.endline + 'cpm/x86_64'
     ),
    ('trigger_cmd ATCN executed successfully',
     'executed' + TestCli.endline + 'successfully'
     ),
    ('trigger_cmd device_info MyDevice v0.0.1 SN123456',
     'MyDevice' + TestCli.endline + 'v0.0.1' + TestCli.endline + 'SN123456'
     )
])
def test_send_command(cli, command, expected):
    response = cli.send_command(command)
    assert response == expected
