""" Serial package exceptions """


class SerialConnectionError(OSError):
    """ Subclass for serial connections errors """


class SerialNoMatchError(SerialConnectionError):
    """ Subclass for serial read operation errors """

    def __init__(self, expected, timeout, output):
        self.expected = expected
        self.timeout = timeout
        self.output = output
        super(SerialNoMatchError, self).__init__(self._get_message())

    def _get_message(self):
        msg = 'No match found for "{!r}" in "{}" timeout period.'.format(
            self.expected, self.timeout
        )
        if self.output:
            msg += ' Output: {}'.format(self.output)
        return msg
