""" Serial package entities """

from enum import Enum


class LineBreaks(Enum):
    """ Line breaks """
    LF = '\n'
    CR = '\r'
    CRLF = '\r\n'

    def __str__(self):
        return '{}'.format(self.value)

    @classmethod
    def list(cls):
        return [str(attr) for attr in cls]

    @classmethod
    def string(cls):
        return ','.join(cls.list())

    @classmethod
    def has_value(cls, value):
        return True if str(value) in cls.list() else False
