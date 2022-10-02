""" Cambrionix Command Line API """

import time
from functools import wraps
from .entities.cli import (
    CambrionixCli,
    StateParser,
    TerminalCommands
)
from .entities.hub import UsbHub
from .utils import Configuration
from .logger import get_logger
from .terminal.connection import LineBreaks
from .terminal.exceptions import SerialConnectionError


LOGGER = get_logger(__name__)


def cbrxcommand(delay=None):
    def deco(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                seconds = getattr(self.__class__, str(delay))
            except AttributeError:
                seconds = 0.0
            command = func(self, *args, **kwargs)
            try:
                response = self.serial.send_command(command)
            except SerialConnectionError as e:
                if 'Device not configured' not in str(e):
                    raise e
                self.log('{}, trying to recover in {} seconds...'.format(e, seconds))
                self.serial.stop()
                time.sleep(seconds)
                self.serial.start()
                response = self.serial.send_command('')
            else:
                time.sleep(seconds)
            return response
        return wrapper
    return deco


# pylint: disable=no-self-use
class Cambrionix(UsbHub):
    """
    Represents an PPxx/Uxx Cambrionix USB Hub.

    :param int R_DELAY: *reboot* command time delay factor.
    :param int M_DELAY: *set_mode* command time delay factor.
    """

    R_DELAY = 10
    M_DELAY = 11

    def __init__(self,
                 port,
                 serial_speed='slow',
                 prompt='>>',
                 default_enter=LineBreaks.CRLF,
                 response_return=LineBreaks.CRLF,
                 **kwargs):
        r"""
        Initialize an Cambrionix instance.

        Interaction with Cambrionix USB Hub is performed through serial CLI.

        :param str port: Serial port name.
        :param str serial_speed: Serial speed, slow (115200) or fast (1000000).
        :param str prompt: Serial command line prompt.
        :param str default_enter: Executed serial command line terminator.
        :param str response_return: Serial command response line terminator.
        :param **kwargs: Any other serial cli attributes such as encoding, read/write timeout etc.
        """
        self._serial = CambrionixCli(port,
                                     serial_speed=serial_speed,
                                     prompt=prompt,
                                     default_enter=default_enter,
                                     response_return=response_return,
                                     **kwargs)
        super(Cambrionix, self).__init__()

    @staticmethod
    def _listMethods():  # pylint: disable=invalid-name
        """
        Cambrionix XML-RPC server introspection API.

        .. note::

            Cambrionix XML-RPC API methods should be added here.

        """
        return [
            'connect',
            'system_monitor',
            'show_state',
            'set_mode',
            'help',
            'reboot',
            'disconnect'
        ]

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def __repr__(self):
        return "{}('{}')".format(
            self.__class__.__name__,
            self.serial.port
        )

    @property
    def serial(self):
        """ Serial CLI """
        return self._serial

    @property
    def log(self):
        """ Message logging """
        return self._log

    @property
    def help(self):
        """ Command line help information """
        return self._help()

    @property
    def system(self):
        """ Show hardware and firmware information """
        return self._system()

    @property
    def health(self):
        """ Show voltages, temperature, errors and boot flag """
        return self._health()

    @property
    def limits(self):
        """ Show voltage and temperature limits """
        return self._limits()

    @property
    def cef(self):
        """ Clear Error Flags from each USB port """
        return self._cef()

    @property
    def crf(self):
        """ Clear Reboot Flag """
        return self._crf()

    @classmethod
    def from_ini(cls, host, ini_file):
        r"""
        Initialization through a **INI** configuration file.

        ``INI`` structure:

        ``
        [<hostname>:cbrx:serial]
        option1=value1
        option2=value2
        ``

        :param str host: Cambrionix host computer.
        :param str ini_file: Relative or absolute path.
        :returns: :class: An `Cambrionix` instance.
        :raises ConfigurationError: Missing configuration file path.
        :raises ConfigurationSectionError: Invald section name.
        """
        c = Configuration(host, ini_file)
        c.read()
        return cls(**c.items())

    def connect(self):
        """
        Connect to Cambrionix Serial CLI.

        :returns: Nothing.
        :raises SerialConnectionError: Failure of serial connection.
        """
        self.serial.start()
        self.log('connected')

    def system_monitor(self):
        """
        Method displays:

        - Hardware and software information.
        - Voltage, temparature, errors.
        - Potential system reboots.
        - Voltage and temperature limits.

        :returns str: Perfomance and system resources.
        """
        return '\n'.join(
            [self.system, self.health, self.limits]
        )

    def reboot(self, watchdog=True):
        """
        Reboots the firmware (USB port controllers not fully reset).

        .. note::

            After a reboot, the USB serial port connection to the host
            is reset. This will result in a terminal emulator shutting the
            serial connection.

        :param bool watchdog: If ``False`` reboot is executed immediately
            else system will lock into an infinite unresponsive loop until
            the watchdog timer expires.
        :returns: Nothing.
        :raises GeneralError: Generic cli error.
        :raises FatalError: Fatal cli error.
        """
        self._reboot(watchdog=watchdog)
        self.log('Rebooted')

    def show_state(self, port_index=None):
        """
        Show the state for an USB port or all ports.

        :param int_or_None port_index: Port number or all ports if omitted.
        :returns str: The status/state of port or all ports.
        :raises GeneralError: Generic cli error.
        :raises FatalError: Fatal cli error.
        :raises ValueError: Port attribute value errors.
        """
        state = self._get_state(port_index)
        return str(state)

    def set_mode(self, mode, port_index=None):
        """
        Set the mode for an single USB port or all ports.

        ..  hint::

            When port is placed in an **particular mode**, the port
            will transition from one state to another according to
            whether the device **is attached**, and whether the device
            **is charging or not**.

        :param str mode: Port mode, OFF, SYNC, BIASED, CHARGED.
        :param int port_index: Port index or all ports.
        :returns str: The status/state of port or all ports.
        :raises GeneralError: Generic CLI error.
        :raises FatalError: Fatal CLI error.
        """
        index = port_index or 'ALL'
        self.log("setting Port:'{}' mode to:'{}'".format(index, mode))
        self._mode(mode, port_index)

    def disconnect(self):
        """
        Disconnect from Cambrionix serial CLI.

        :returns: Nothing.
        """
        self.serial.stop()
        self.log('disconnected')

    @cbrxcommand()
    def _help(self):
        return TerminalCommands.help()

    @cbrxcommand()
    def _limits(self):
        return TerminalCommands.limits()

    @cbrxcommand()
    def _health(self):
        return TerminalCommands.health()

    @cbrxcommand()
    def _system(self):
        return TerminalCommands.system()

    @cbrxcommand(delay='R_DELAY')
    def _reboot(self, watchdog=True):
        return TerminalCommands.reboot(watchdog=watchdog)

    @cbrxcommand()
    def _state(self, port_index=None):
        return TerminalCommands.state(port_index)

    @cbrxcommand(delay='M_DELAY')
    def _mode(self, mode, port_index):
        return TerminalCommands.mode(mode, port_index)

    @cbrxcommand()
    def _cef(self):
        return TerminalCommands.cef()

    @cbrxcommand()
    def _crf(self):
        return TerminalCommands.crf()

    def _get_state(self, port_index=None):
        self._set_state(port_index)
        if port_index is None:
            return self.ports
        return super(Cambrionix, self).search_port(port_index)

    def _set_state(self, port_index=None):
        response = self._state(port_index)
        ports = StateParser(response).process()
        for index, port in ports:
            super(Cambrionix, self).new_port(index)
            super(Cambrionix, self).update_port(index, **port)

    def _log(self, action, log=True):
        if log:
            LOGGER.info(
                "Serial CLI to:'%s' %s", self.serial.port, action
            )
