""" Module encapsulates the access for Serial ports """

import collections
import codecs
import serial
import six
from .exceptions import (
    SerialConnectionError,
    SerialNoMatchError
)
from .entities import LineBreaks


DEFAULT_SETTINGS = serial.SerialBase(
    baudrate=9600,
    timeout=1.0,
    write_timeout=1.0,
    inter_byte_timeout=0.0
).get_settings()


# pylint: disable=dangerous-default-value
# pylint: disable=attribute-defined-outside-init
class SerialConnection(object):
    """ Represents an Serial connection """

    def __init__(self,
                 port,
                 newline=LineBreaks.LF,
                 encoding='utf-8',
                 encoding_errors='strict',
                 **kwargs):
        """
        Initialize an Serial connection.

        :param str port: Serial port name.
        :param str newline: Data terminator for read and write operations.
        :param str encoding: Data enconding type.
        :param str encoding_errors: Data enconding mode.
        :param kwargs: Can be used to set library-instance-wide default value
            to create new connection instance internally
        """
        self.port = port
        self.newline = newline
        self._encoding = encoding
        self._encoding_errors = encoding_errors
        self._defaults = dict(DEFAULT_SETTINGS)
        self.set_default_parameters(kwargs)
        self._conn = None

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        if port is None or not isinstance(port, six.string_types):
            raise ValueError(
                "'port' name must be a string, not {}".format(type(port))
            )
        self._port = port

    @property
    def newline(self):
        return self._newline

    @newline.setter
    def newline(self, newline):
        newline = codecs.unicode_escape_decode(str(newline))[0]
        if not LineBreaks.has_value(newline):
            raise ValueError(
                "'newline' should be one of: {!r}".format(LineBreaks.string())
            )
        self._newline = newline

    def open(self):
        """ Open an serial connection to the specified serial port """
        if self._conn is not None:
            if self._conn.is_open:
                raise SerialConnectionError(
                    'Serial connection is already open to: {}'.format(self._port)
                )
        try:
            # Pyserial opens the serial port at constructor
            self._conn = serial.Serial(self._port, **self._defaults)
        except serial.SerialException as e:
            self._conn = None
            raise SerialConnectionError(e)

    def close(self):
        """ Terminate the serial connection """
        if self._conn is not None:
            if self._conn.is_open:
                self._conn.close()
            self._conn = None

    def write(self, data, encoding=None):
        """
        Writes the given data into the serial connection output buffer.

        .. note::

            Method does not return the possible output of the executed command.
            Method consumes the written text until the added newline from the output.

        :param str data: The data to write over the serial connection.
        :param str encoding: Data encoding type, defaults: ``utf-8``.
        :returns str: The written data.
        :raises SerialConnectionError: Unxpected connection errors.
        :raises SerialNoMatchError: Failure to consume the written data.
        """
        self._verify()
        if self._newline in data:
            raise RuntimeError(
                "'Write' operation cannot be used with data "
                "containing the selected newline as line terminator. "
                "Use 'Write bare instead.'"
            )
        self.write_bare('{}{}'.format(data, self._newline), encoding)
        return self.read_until(self._newline, encoding)

    def write_bare(self, data, encoding=None):
        """
        Writes the given data and nothing else, into the connection.

        .. note::

            Method does not append a **newline** nor consume the written text.

        :param str data: Data to write on the outgoing serial connection buffer.
        :param str encoding: Data encoding type, defaults: ``utf-8``.
        :returns: Nothing.
        :raises SerialConnectionError: Unexpected connection errors.
        """
        self._verify()
        try:
            self._conn.write(self._encode(data, encoding))
        except serial.SerialException as e:
            raise SerialConnectionError(e)

    def read(self, encoding=None):
        """
        Reads everything that is currently available in the incoming buffer.

        :param encoding str: Data encoding type, defaults: ``utf-8``.
        :returns str: Everything from the serial connection.
        :raises SerialConnectionError: Unexpected connection errors.
        """
        self._verify()
        try:
            output = self._decode(self._conn.read_all(), encoding)
        except serial.SerialException as e:
            raise SerialConnectionError(e)
        else:
            return output

    def read_until(self, expected, encoding=None):
        """
        Reads incoming buffer until ``expected`` text is encountered.

        :param str expected: The expected text.
        :param str encoding: Data encoding type, defaults: ``utf-8``.
        :returns str: All data up to expected text.
            How match to wait for the output depends on the
            serial connection ``timeout`` parameter.
        :raises SerialConnectionError: Unexpected connection errors.
        :raises SerialNoMatchError: If the expected text is not found.
        """
        success, output = self._read_until(expected, encoding)
        if not success:
            raise SerialNoMatchError(
                expected, self._defaults.get('timeout'), output
            )
        return output

    def set_default_parameters(self, params):
        """
        Updates default parameters with given dictionary.
        Values can be in any types and are converted into
        appropreate type.

        .. note::

            Only supported parameters are taken into account,
            while others are ignored silently.

        :param dict params:
        :return dict:
        """
        prev_value = collections.OrderedDict(self._defaults)
        for key, value in params.items():
            if key in self._defaults:
                value_type = type(self._defaults.get(key))
                self._defaults[key] = value_type(value)
        return prev_value

    def reset_default_parameters(self):
        """
        Reset default parameters to those defined in serial.SerialBase.

        .. note::

            Does not directly affect the existing serial port.

        """
        self._defaults = dict(DEFAULT_SETTINGS)

    def _verify(self):
        """ Check the Serial connection openess """
        if self._conn is None:
            raise SerialConnectionError(
                'No Serial connection open'
            )

    def _read_until(self, expected, encoding=None):
        """ Read until an expected text """
        self._verify()
        expected = self._encode(expected, encoding)
        try:
            output = self._decode(
                self._conn.read_until(expected=expected),
                encoding
            )
        except serial.SerialException as e:
            raise SerialConnectionError(e)
        else:
            success = output.endswith(
                self._decode(expected, encoding)
            )
            return (success, output)

    def _encode(self, ustring, encoding=None, encoding_errors=None):
        """ Encode (unicode) string into raw bytes """
        return ustring.encode(
            encoding or self._encoding,
            encoding_errors or self._encoding_errors
        )

    def _decode(self, bstring, encoding=None, encoding_errors=None):
        """ Decode raw bytes to (unicode) string."""
        return bstring.decode(
            encoding or self._encoding,
            encoding_errors or self._encoding_errors
        )
