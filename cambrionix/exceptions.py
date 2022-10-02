""" Cambrionix exceptions """


class CambrionixError(Exception):
    """ Base class for Cambrionix errors """


class ConfigurationError(CambrionixError):
    """ Subclass for Cambrionix configuration file errors """


class ConfigurationSectionError(ConfigurationError):
    """ Subclass of configuration file errors """


class CommandLineError(CambrionixError):
    """ Subclass for Cambrionix CLI errors """

    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
        super(CommandLineError, self).__init__(self._get_message())

    def _get_message(self):
        msg = (
            "Command execution failed.\nError code: {}.\nReason: {}'"
            .format(self.code, self.reason)
        )
        return msg


class GenericError(CommandLineError):
    """ Subclass for generic CLI errors """


class FatalError(CommandLineError):
    """ Subclass for fatal CLI errors """
