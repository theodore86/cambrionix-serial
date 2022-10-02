"""

******************
Cambrionix USB HUB
******************

Supports the Universal Series:

* PPxx
* Uxx
* ThunderSync

"""

import collections
import enum
import warnings


class UsbHub(object):
    """ Represents the Cambrionix USB Hub """

    def __init__(self):
        """ Initialize the USB Hub ports """
        self._ports = PortList()

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def __str__(self):
        return str(self._ports)

    def __len__(self):
        return len(self._ports)

    @property
    def ports(self):
        return self._ports

    def search_port(self, index):
        """
        Return the port given an index value.

        :param int index: The port index.
        :returns Port_or_None: Port or nothing.
        """
        return self._ports.search_by_index(index)

    def new_port(self, index):
        """
        Create a new port and add it to the list.

        :param int index: The port index.
        :returns: Nothing
        :raises ValueError: In case of invalid index type.
        """
        port = self.search_port(index)
        if port is None:
            p = Port(index)
            self._ports.append(p)

    def update_port(self, index, **kwargs):
        r"""
        Update port attributes.

        Attributes could be:

        #. Flags (system, state, mode)
        #. Profile ID
        #. Energy
        #. Time charging
        #  Time charged
        #. Current milliamperes

        .. seealso::  :class:`Port`

        .. note::

            Invalid port attributes are silently ignored.

        :param int index: The port index.
        :param **kwargs: Port attributes as keyword arguments.
        :raises ValueError: In case of invalid index type.
        :raises IndexError: In case of non-existing port.
        """
        port = self.search_port(index)
        if port is None:
            raise IndexError(
                "Port:'{}' is not found, "
                "should be added as new port".format(index)
            )
        if not kwargs:
            kwargs = {}
            warnings.warn(
                "Port:'{}' remains unmodified.".format(port.index),
                stacklevel=2
            )
        for attrib, value in kwargs.items():
            if hasattr(port, attrib):
                setattr(port, attrib, value)

    def remove_port(self, index):
        """
        Removes a port from the port list.

        :param int index: The port index.
        :returns Port_or_None: The ``Port`` that has been removed
            from the list or ``None`` if does not exist.
        :raises ValueError: In case of invalid index type.
        """
        port = self.search_port(index)
        if port is not None:
            self._ports.remove(port)
        return port


class PortList(list):
    """ Represents the list of USB HUB ports """

    def __str__(self):
        ports = sorted(self, key=lambda p: p.index)
        return '\n\n'.join(
            [str(port) for port in ports]
        )

    def search_by_index(self, index):
        """
        Return the port with the given index.

        :param int index: The index of a port.
        :returns Port_or_None:
        :raises ValueError: In case of invalid index type.
        """
        try:
            index = int(index)
        except TypeError:
            raise ValueError(
                "Not a valid 'index':{!r}".format(index)
            )
        else:
            _port = None
            for port in self:
                if port.index == index:
                    _port = port
                    break
            return _port

    def search_by_flag(self, flag):
        """
        Return a list of ports having the given flag.

        .. seealso::  :class:`PortFlags`

        :param str flag: A port flag.
        :returns list: An empty list or a list of :class:`Port` (s).
        """
        ports = []
        for port in self:
            values = vars(port.flags).values()
            if str(flag) in values:
                ports.append(port)
        return ports


# pylint: disable=attribute-defined-outside-init
class Port(object):
    """ Represents an Cambrionix USB port """

    def __init__(self,
                 index,
                 current_ma=0.0,
                 flags=None,
                 profile_id=0,
                 time_charging=0,
                 time_charged='x',
                 energy=0.0):
        """
        Initialize an USB port.

        :param int index: The port number.
        :param int current_ma: Current delivered to the attached device (amperes).
        :param PortFlags flags: A Portflags object.
        :param int profile_id: Unique profile ID number for the given port.
        :param int time_charging: Time in seconds the port has been charging for.
        :param int time_charged: Time in seconds the port has been charged for.
        :param float energy: Energy the device has consumed (watthours).
        :raises ValueError: In case of invalid parameter values.
        """
        self.index = index
        self.current_ma = current_ma
        self.flags = flags
        self.profile_id = profile_id
        self.time_charging = time_charging
        self.time_charged = time_charged
        self.energy = energy

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def __str__(self):
        attribs = []
        for attr, val in vars(self).items():
            attr, val = attr.lstrip('_'), str(val)
            attribs.append('{}:{}'.format(attr, val))
        state = '\n'.join(attribs)
        return state

    def __eq__(self, other):
        if not isinstance(other, Port):
            return False
        return self.index == other.index

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        try:
            index = int(index)
        except TypeError:
            raise ValueError(
                "Not a valid 'index':{!r}".format(index)
            )
        else:
            if index < 0:
                raise ValueError(
                    "Not a valid 'index':{!r}".format(index)
                )
            self._index = index

    @property
    def current_ma(self):
        return self._current_ma

    @current_ma.setter
    def current_ma(self, ma):
        try:
            ma = int(ma)
        except TypeError:
            raise ValueError(
                "Not a valid 'milliamperes':{!r}".format(ma)
            )
        else:
            self._current_ma = (ma / 1000)  # milliamperes -> amperes

    @property
    def flags(self):
        return self._flags

    @flags.setter
    def flags(self, flags):
        if (flags is not None
                and not isinstance(flags, PortFlags)):
            raise ValueError(
                "Not a valid 'flags':{!r} value".format(flags)
            )
        self._flags = flags or PortFlags('O', 'D')

    @property
    def profile_id(self):
        return self._profile_id

    @profile_id.setter
    def profile_id(self, _id):
        try:
            _id = int(_id)
        except TypeError:
            raise ValueError(
                "Not a valid 'profile_id':{!r}".format(_id)
            )
        else:
            if _id < 0:
                raise ValueError(
                    "Not a valid 'profile_id':{!r}".format(_id)
                )
            self._profile_id = _id

    @property
    def time_charging(self):
        return self._time_charging

    @time_charging.setter
    def time_charging(self, time):
        try:
            time = int(time)
        except TypeError:
            raise ValueError(
                "Not a valid 'time_charging':{!r}".format(time)
            )
        else:
            if time < 0:
                raise ValueError(
                    "Not a valid 'time_charging':{!r}".format(time)
                )
            self._time_charging = time

    @property
    def time_charged(self):
        return self._time_charged

    @time_charged.setter
    def time_charged(self, time):
        try:
            time = int(time)
        except (ValueError, TypeError):
            try:
                TimeCharged(time)  # Test if 'x'
            except ValueError:
                raise ValueError(
                    "Not a valid 'time_charged':{!r}".format(time)
                )
        else:
            if time < 0:
                raise ValueError(
                    "Not a valid 'time_charged':{!r}".format(time)
                )
        self._time_charged = time

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, consumed):
        try:
            consumed = float(consumed)
        except TypeError:
            raise ValueError(
                "Not a valid 'energy' value:{!r}".format(consumed)
            )
        else:
            if consumed < 0:
                raise ValueError(
                    "Not a valid 'energy' value:{!r}".format(consumed)
                )
            self._energy = '{0:.2f}'.format(consumed)  # precision 0.00


class PortFlags(object):
    """ USB Port flags """

    def __init__(self, mode, state, *system):
        r"""
        Initialize USB port flags.

        .. seealso::  :class:`Mode`, :class:`State`, :class:`System`

        :param str mode: Mode flag.
        :param str state: State flag.
        :param *system: System flags.
        :raises ValueError: In case of invalid port flag.
        """
        self.mode = mode
        self.state = state
        self.system = system

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)

    def __str__(self):
        flags = '{} {} {}'.format(
            self.system, self.state, self.mode
        )
        return flags.strip()

    def __eq__(self, other):
        return (self.system == other.system
                and self.state == other.state
                and self.mode == other.mode)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def system(self):
        return self._system

    @system.setter
    def system(self, system):
        for f in iter(system):
            if not System.has_value(f):
                raise ValueError(
                    "Not a valid 'system' flag: {!r}".format(f)
                )
        self._system = ' '.join(system)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if not State.has_value(state):
            raise ValueError(
                "Not a valid 'state' flag: {!r}".format(state)
            )
        self._state = state

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if not Mode.has_value(mode):
            raise ValueError(
                "Not a valid 'mode' flag: {!r}".format(mode)
            )
        self._mode = mode


class Flags(enum.Enum):

    @classmethod
    def names(cls):
        return set(flag.name for flag in cls)

    @classmethod
    def values(cls):
        return set(flag.value for flag in cls)

    @classmethod
    def has_value(cls, value):
        return value in cls.values()


Charge = collections.namedtuple(
    'CHARGE', ['profiling', 'idle', 'charging', 'finished']
)


class Mode(Flags):
    """
    CHARGE mode flags:

    * P = Profiling
    * I = IDLE
    * C = Charging
    * F = Finished
    """
    OFF = 'O'
    SYNC = 'S'
    BIASSED = 'B'
    CHARGE = Charge('P', 'I', 'C', 'F')

    @classmethod
    def has_value(cls, value):
        found = False
        for _value in cls.values():
            if isinstance(_value, Charge):
                if value in list(_value):
                    found = True
                    break
            elif value == _value:
                found = True
                break
        return found


class State(Flags):
    ATTACHED = 'A'
    DETACHED = 'D'


class System(Flags):
    THEFT = 'T'
    ERROR = 'E'
    REBOOT = 'R'
    RESET = 'r'


class TimeCharged(enum.Enum):
    NOT_VALID = 'x'
