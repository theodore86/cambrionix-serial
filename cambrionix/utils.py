""" Cambrionix package utilities """

from six.moves import configparser
from .exceptions import (
    ConfigurationError,
    ConfigurationSectionError
)


class Configuration(object):
    """
    Cambrionix configuration parameters throguh ``INI`` file.

    :param str host: Hostname, the host where cambrionix is directly connected.
    :param str config: ``INI`` file path.
    """

    SUBSECTION = 'cbrx:serial'
    PARSER = configparser.ConfigParser()

    def __init__(self, host, config):
        self._host = host
        self._config = config

    @property
    def section(self):
        return '{}:{}'.format(
            self._host, self.__class__.SUBSECTION
        )

    def read(self):
        """
        Read Cambrionix INI configuration file.

        :returns: Nothing.
        :raises ConfigurationError: Non-existing configuration.
        """
        read_ok = self.__class__.PARSER.read(self._config)
        if not read_ok:
            raise ConfigurationError(
                "Configuration file '{}' not found".format(self._config)
            )

    def items(self):
        """
        Get all ``INI`` option value pairs for the given section.

        :returns dict: A dictionary of option values for the given section.
        :raises ConfigurationSectionError: In case section is invalid.
        """
        try:
            items = self.__class__.PARSER.items(self.section)
        except configparser.NoSectionError:
            raise ConfigurationSectionError(
                "Invalid section, should be <host>:{}"
                .format(self.__class__.SUBSECTION)
            )
        else:
            return dict(items)
