"""

*********************************
Cambrionix Command Line Interface
*********************************

Module to control devices in the Universal Series:

* PPxx
* Uxx
* Thundersync

Built-in commands are executed through an serial port (UART).

"""

import re
from enum import Enum
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from six import add_metaclass, string_types
from six.moves import zip
from ..exceptions import GenericError, FatalError
from .hub import PortFlags, Mode
from ..terminal.connection import LineBreaks
from ..terminal.cli import SerialCli


class Speed(Enum):
    slow = 115200
    fast = 1000000

    @classmethod
    def members(cls):
        return ' or '.join([
            '{} ({})'.format(m.name, m.value)
            for m in cls.__members__.values()
        ])

    @classmethod
    def rate(cls, name):
        m = getattr(cls, name, None)
        return m.value if m is not None else None

    @classmethod
    def has_rate(cls, name):
        return True if name in cls.__members__ else False


# pylint: disable=attribute-defined-outside-init
class CambrionixCli(SerialCli):
    """ Represents the CLI for the Cambrionix Universal Chargers """

    def __init__(self,
                 port,
                 serial_speed='slow',
                 prompt='>>',
                 default_enter=LineBreaks.CRLF,
                 response_return=LineBreaks.CRLF,
                 **kwargs):
        r"""
        :param str port: The serial port name.
        :param str serial_speed: The serial speed, slow (115,2Kbaud) or fast(1Mbaud).
        :param str prompt: The serial command line prompt.
        :param str default_enter: Executed serial command line terminator.
        :param str response_return: Serial command line responses line terminator.
        :param **kwargs: Can be used to set library-instance-wide values
            to create new cli instance internally.
        :raises ValueError: In case of invalid serial port name.
        """
        self.serial_speed = serial_speed
        super(CambrionixCli, self).__init__(port,
                                            baudrate=self.serial_speed,
                                            prompt=prompt,
                                            default_enter=default_enter,
                                            response_return=response_return,
                                            **kwargs)

    def __repr__(self):
        return "{}('{}')".format(
            self.__class__.__name__,
            self.port
        )

    @property
    def serial_speed(self):
        return self._serial_speed

    @serial_speed.setter
    def serial_speed(self, speed):
        if (not isinstance(speed, string_types)
                or not Speed.has_rate(speed)):
            raise ValueError(
                "'serial_speed' should be: {}".format(Speed.members())
            )
        self._serial_speed = Speed.rate(speed)

    def send_command(self, command, encoding=None):
        """
        Method to execute/send commands over the cambrionix serial CLI.

        :param str command: The command to be send over the serial port/conection.
        :param str encoding: The data encoding type.
        :returns str: The response output of the executed command.
        :raises GenericError: Any command line errors.
        :raises FatalError: Fatal only command line errors.
        """
        response = self._send_command(command, encoding)
        CliValidator.validate(response)
        return response


class CliValidator(Enum):
    """ Cambrionix CLI response validator """

    GENERIC_ERROR = (re.compile(r'^\*E(\d{3}):\s+?(.*)$'), GenericError)
    FATAL_ERROR = (re.compile(r'^\*FATAL.*?E(\d{3}):\s+?(.*)$'), FatalError)

    @classmethod
    def validate(cls, response):
        """
        Validate Cambrionix command line responses.

        :param str response: Command line response output.
        :returns: Nothing.
        :raises GenericError: Errors of the form: ``*Ennn: Errortext``.
        :raises FatalError: Errors of the form: ``*FATAL ERROR Ennn: Error text``.
        """
        for attr in cls:
            pattern, error = attr.value
            result = pattern.search(response)
            if result is not None:
                code, reason = result.groups()
                raise error(code, reason)


# pylint: disable=attribute-defined-outside-init
@add_metaclass(ABCMeta)
class CliResponseParser(object):
    """ Represents an CLI response parser """

    def __init__(self, response, newline=LineBreaks.CRLF, linesep=None):
        """
        Initialize an Cambrionix CLI response parser.

        :param str response: Text response from Cambrionix CLI.
        :param str newline: Line break.
        :param str linesep: Line separator.
        :raises ValueError: Command response not in the appropriate format.
        """
        self.response = response
        self.newline = newline
        self.linesep = linesep

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        if (response is None
                or not isinstance(response, string_types)):
            raise ValueError(
                "'response' must be a string not {}".format(type(response))
            )
        self._response = response

    @property
    def newline(self):
        return self._newline

    @newline.setter
    def newline(self, newline):
        if not LineBreaks.has_value(newline):
            raise ValueError(
                "'newline' should be one of: {!r}".format(LineBreaks.string())
            )
        self._newline = str(newline)

    @staticmethod
    def _strip(values, char=None):
        """ List of values to strip leading and trailing char """
        return [
            value.strip(char) for value in values
        ]

    def readlines(self):
        """ Return an generator with the reading lines """
        return (
            line.strip() for line in self.response.split(self.newline)
        )

    def countlines(self):
        """ Return total number of lines """
        lines = 0
        for _ in self.readlines():
            lines += 1
        return lines

    def splitlines(self, maxsplit=-1):
        """
        Split each line based on the given line separator.

        :param int maxsplit: At most ``maxsplit`` splits are done.
        """
        for line in self.readlines():
            yield self._strip(line.split(self.linesep, maxsplit))

    @abstractmethod
    def process(self):
        pass


class StateParser(CliResponseParser):
    """
    ``show state [p]`` command response parser.

    .. note::

        #. One line per port.
        #. By default command separated fields per line.

    """

    keys = ('current_ma',
            'flags',
            'profile_id',
            'time_charging',
            'time_charged',
            'energy')

    def __init__(self, response, newline=LineBreaks.CRLF, linesep=','):
        super(StateParser, self).__init__(response, newline, linesep)

    def _map_line_values_to_keys(self):
        for values in super(StateParser, self).splitlines():
            if len(self.__class__.keys) != len(values[1:]):
                raise ValueError(
                    "Row format: '{!r}' is not valid".format(values)
                )
            _port_dict = OrderedDict(
                zip(self.__class__.keys, values[1:])
            )
            yield (values[0], _port_dict)

    @staticmethod
    def _process_flags(flags):
        flags = flags.split()
        flags.reverse()
        return PortFlags(*flags)

    def process(self):
        """
        Map each line value to predefined keys.

        :return tuple: Port index and attributes.
        """
        ports = self._map_line_values_to_keys()
        for index, port_map in ports:
            flags = self._process_flags(port_map['flags'])
            port_map['flags'] = flags
            yield (index, port_map)


class TerminalCommands(Enum):
    """
    Commands that are issued to the Cambrionix CLI (serial port)
    are referred to as **terminal commands**.
    """
    STATE_A = 'state'
    STATE_P = 'state {}'
    MODE_A = 'mode {}'
    MODE_P = 'mode {} {}'
    REBOOT = 'reboot'
    REBOOT_W = 'reboot watchdog'
    SYSTEM = 'system'
    HEALTH = 'health'
    LIMITS = 'limits'
    CEF = 'cef'
    CRF = 'crf'
    HELP = 'help'

    def __str__(self):
        return '{}'.format(self.value)

    @classmethod
    def reboot(cls, watchdog=False):
        """ Reboot [watchdog] terminal command """
        if watchdog:
            return str(cls.REBOOT_W)
        return str(cls.REBOOT)

    @classmethod
    def state(cls, port=None):
        """ State [p] terminal command """
        if port is None:
            return str(cls.STATE_A)
        return str(cls.STATE_P).format(port)

    @classmethod
    def mode(cls, mode, port=None):
        """ Mode <m> [p] terminal command """
        if mode in Mode.names():
            mode = mode[0]
        mode = mode.lower()
        if port is None:
            return str(cls.MODE_A).format(mode)
        return str(cls.MODE_P).format(mode, port)

    @classmethod
    def system(cls):
        """ System terminal command """
        return str(cls.SYSTEM)

    @classmethod
    def health(cls):
        """ Health terminal command """
        return str(cls.HEALTH)

    @classmethod
    def limits(cls):
        """ Limits terminal command """
        return str(cls.LIMITS)

    @classmethod
    def cef(cls):
        """ Clear error flags terminal command """
        return str(cls.CEF)

    @classmethod
    def crf(cls):
        """ Clear reboot flag terminal command """
        return str(cls.CRF)

    @classmethod
    def help(cls):
        """ Help terminal command """
        return str(cls.HELP)
