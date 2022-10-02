""" Unit tests for serial connection class """

import pytest
import serial_mock
from cambrionix.terminal.connection import SerialConnection
from cambrionix.terminal.exceptions import SerialNoMatchError
from cambrionix.terminal.entities import LineBreaks


class TestConnection(serial_mock.MockSerial):
    """ Test Serial interface (StringIO) """
    delimiter = ''
    endline = ''
    prompt = ''

    @serial_mock.serial_query("cmd")
    def trigger_cmd(self, *result):
        return ' '.join(result)


@pytest.fixture(scope='session')
def conn(dummy_serial, monkeysession):
    conn = SerialConnection('/dev/ttyUSB0')
    monkeysession.setattr(conn, '_conn', dummy_serial(TestConnection))
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def test_setup_teardown(conn):
    yield
    conn.read()
    conn.reset_default_parameters()


@pytest.mark.parametrize('response', [
    r'test_string_output\r',
    r'5,0000,RDO,0,0,x,0.00\n',
    r'*E400 Invalid command\r\n'
])
def test_read_data(conn, response):
    conn.write_bare('cmd {}'.format(response))
    assert conn.read() == response


@pytest.mark.parametrize('response, expected', [
    (r'\rtest', r'\r'),
    (r'an long string\r\nwithout', r'an long string\r\n'),
    (r'clearing\rthe output', r'clearing\r'),
    (r'buffer\noutput test...\n,', r'buffer\n'),
])
def test_read_until_data(conn, response, expected):
    conn.write_bare('cmd {}'.format(response))
    assert conn.read_until(expected) == expected


@pytest.mark.parametrize('response, expected', [
    (r'\ntesting', r'\r'),
    (r'read until\n', r'\ntesting'),
    (r'5,0000,RDO', r'RDOF')
])
def test_read_until_timeout(conn, response, expected):
    conn.write_bare('cmd {}'.format(response))
    with pytest.raises(SerialNoMatchError) as e:
        conn.read_until(expected)
    assert e.value.output == response
    assert e.value.expected == expected


@pytest.mark.parametrize('params, expected', [
    ({'timeout': 0.01, 'write_timeout': 2, 'baudrate': 115200, 'test_key': 'value'},
     {'timeout': 0.01, 'write_timeout': 2, 'baudrate': 115200}
     ),
    ({'test_key1': 'value_1', 'test_key2': 'value_2', 'inter_byte_timeout': 0.1},
     {'inter_byte_timeout': 0.1}
     ),
    ({'key1': 'value1', 'key2': 'value2'}, {})
])
def test_set_default_parameters(conn, params, expected):
    defaults = conn.set_default_parameters(params)
    diff = dict(set(conn._defaults.items()) - set(defaults.items()))
    assert diff == expected


@pytest.mark.parametrize('data', ['writing to output buffer'])
@pytest.mark.parametrize('newline', LineBreaks.list())
def test_newline_in_write_data(conn, data, newline):
    with pytest.raises(RuntimeError):
        conn.newline = newline
        conn.write('cmd {}{}'.format(data, newline))


@pytest.mark.parametrize('char, should_raise', [
    (str(LineBreaks.LF), False),
    (str(LineBreaks.CR), False),
    (str(LineBreaks.CRLF), False),
    (r'\n\n', True),
    (r'\r\n\r', True),
    (r'\r\r', True)
])
def test_newline_character(conn, char, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            conn.newline = char
    else:
        conn.newline = char
