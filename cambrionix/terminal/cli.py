""" Serial Command Line Interface """

import abc
import codecs
import six
import serial
import serial.tools.list_ports as ports
from .connection import SerialConnection
from .entities import LineBreaks


# pylint: disable=attribute-defined-outside-init
@six.add_metaclass(abc.ABCMeta)
class SerialCli(object):
    """
    Represents an Abstract Serial Command Line Interface.
    Any device/subclass with serial CLI should inherit from this class.
    """

    def __init__(self,
                 port,
                 baudrate=9600,
                 prompt='',
                 default_enter=LineBreaks.LF,
                 response_return=LineBreaks.LF,
                 **kwargs):
        r"""
        Initialize an Serial Command Line Interface.

        :param str port: Port serial number or device path.
        :param int baudrate: Serial transmission rate.
        :param str prompt: Data terminator for read operations only.
        :param str default_enter: Terminator character for write operations.
        :param str response_return: Line terminator for command line responses.
        :param **kwargs: Can be used to set library-instance-wide default value
            to create new connection instance internally.
        """
        self.port = port
        self.baudrate = baudrate
        self.prompt = prompt
        self.default_enter = default_enter
        self.response_return = response_return
        self._conn = SerialConnection(
            self.port, newline=self.default_enter,
            baudrate=self.baudrate, **kwargs
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    @abc.abstractmethod
    def send_command(self, command, encoding=None):
        pass

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        success, port = self._is_valid_port(port)
        if not success:
            raise ValueError(
                "Serial port: '{}' is not exist".format(port)
            )
        self._port = port

    @staticmethod
    def _is_valid_port(port):
        is_valid = (False, port)
        for p in ports.comports():
            if p.serial_number == port:
                is_valid = (True, p.device)
            elif p.device == port:
                is_valid = (True, p.device)
        return is_valid

    @property
    def baudrate(self):
        return self._baudrate

    @baudrate.setter
    def baudrate(self, rate):
        try:
            rate = int(rate)
        except TypeError:
            raise ValueError(
                "Not a valid 'baudrate': {!r}".format(rate)
            )
        else:
            if rate not in serial.SerialBase.BAUDRATES:
                raise ValueError(
                    "Not a valid 'baudrate': {!r}".format(rate)
                )
            self._baudrate = rate

    @property
    def prompt(self):
        return self._prompt

    @prompt.setter
    def prompt(self, prompt):
        if prompt is None or not isinstance(prompt, six.string_types):
            raise ValueError(
                "'prompt' must be a string not {}"
                .format(type(prompt))
            )
        self._prompt = prompt

    @property
    def default_enter(self):
        return self._default_enter

    @default_enter.setter
    def default_enter(self, enter):
        enter = codecs.unicode_escape_decode(str(enter))[0]
        if not LineBreaks.has_value(enter):
            raise ValueError(
                "'default_enter' should be one of: {!r}"
                .format(LineBreaks.string())
            )
        self._default_enter = enter

    @property
    def response_return(self):
        return self._response_return

    @response_return.setter
    def response_return(self, response_return):
        response_return = codecs.unicode_escape_decode(str(response_return))[0]
        if not LineBreaks.has_value(response_return):
            raise ValueError(
                "'response_return' should be one of: {!r}"
                .format(LineBreaks.string())
            )
        self._response_return = response_return

    def start(self):
        """ Start the Serial CLI """
        self._conn.open()

    def stop(self):
        """ Stop the Serial CLI """
        self._conn.close()

    def _send_command(self, command, encoding=None):
        """ Execute the given command over the Serial CLI """
        self._conn.read()
        self._conn.write(command, encoding)
        response = self._conn.read_until(self._prompt, encoding)
        return self._sanitize_response(command, response)

    def _sanitize_response(self, command, response):
        """ Sanitize the response of the serial CLI """
        response = self._strip_prompt(response)
        response = self._strip_whitespaces(response)
        response = self._strip_command_echo(command, response)
        return response

    def _split_response_to_lines(self, response):
        """ Split command response to lines """
        return [
            line.strip()
            for line in response.split(self._response_return)
        ]

    def _strip_prompt(self, response):
        """ Strip trailing prompt from the the Serial CLI response """
        lines = self._split_response_to_lines(response)
        last_line = lines[-1]
        if self._prompt in last_line:
            response = self._response_return.join(lines[:-1])
        return response

    def _strip_whitespaces(self, response):
        """ Strip whitespaces/empty lines from the Serial CLI response """
        lines = self._split_response_to_lines(response)
        lines = filter(bool, lines)
        return self._response_return.join(lines)

    def _strip_command_echo(self, command, response):
        """ Strip out command echo from command output."""
        lines = self._split_response_to_lines(response)
        command = command.rstrip(self._response_return)
        if command in lines:
            lines = lines[1:]
        return self._response_return.join(lines)
