"""

**************************************
Cambrionix system and health container
**************************************

Supports the Universal Series:

* PPxx
* Uxx
* ThunderSync

"""

import datetime
import re
import string  # pylint: disable=deprecated-module


# pylint: disable=attribute-defined-outside-init
class System(object):
    """ Hardware and Firmware information """

    DATE_FORMAT = '%b %d %Y %H:%M:%S'
    FIRMWARE_PATTERN = re.compile(r'\d\.\d\d(?:-\S+$)?')
    GROUP_VALUES = ('-', string.ascii_uppercase[:15])

    def __init__(self,
                 hardware,
                 firmware,
                 compiled,
                 group='-',
                 panel_id='Absent',
                 lcd=None):
        """
        Cambrionix system wide parameters.

        :param str hardware: Hardware name.
        :param str firmware: Firmware version sting.
        :param str compiled: Date and time of the firmware.
        :param str group: Group letter read from PCB jumpers.
        :param str_or_int panel_id: Panel ID front panel board.
        :param str lcd: LCD display.
        :raises ValueError: In case of any invalid system value format.
        """
        self.hardware = hardware
        self.firmware = firmware
        self.compiled = compiled
        self.group = group
        self.panel_id = panel_id
        self.lcd = lcd

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def __str__(self):
        attribs = []
        for attrib, value in vars(self).items():
            if value is not None:
                attrib = attrib.lstrip('_').title()
                attribs.append('{}: {}'.format(attrib, value))
        return '\n'.join(sorted(attribs))

    @property
    def firmware(self):
        return self._firmware

    @firmware.setter
    def firmware(self, firmware):
        match_obj = self.__class__.FIRMWARE_PATTERN.match(firmware)
        if match_obj is None:
            raise ValueError(
                "'firmware' version string:{!r} is invalid".format(firmware)
            )
        self._firmware = firmware

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, value):
        if value not in self.__class__.GROUP_VALUES:
            raise ValueError(
                "Not a valid 'group' value:{!r}".format(value)
            )
        self._group = value

    @property
    def compiled(self):
        return self._compiled

    @compiled.setter
    def compiled(self, date):
        try:
            datetime.datetime.strptime(
                date, self.__class__.DATE_FORMAT
            )
        except ValueError:
            raise ValueError(
                "'compiled' date:{!r} has invalid format, "
                "should be: {!r}".format(date, self.__class__.DATE_FORMAT)
            )
        else:
            self._compiled = date
