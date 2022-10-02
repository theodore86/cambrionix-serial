""" Unit tests on cambrionix utilities module """


import pytest
from contextlib import contextmanager
from cambrionix.utils import Configuration
from cambrionix.exceptions import ConfigurationError, ConfigurationSectionError
from .conftest import INI, HOST_A, HOST_B


@contextmanager
def does_not_raise():
    yield


@pytest.mark.parametrize(
    'section, ini_filepath, expectation',
    [
        ('hostA', INI, does_not_raise()),
        ('hostB', 'invalid.ini', pytest.raises(ConfigurationError))
    ],
    indirect=['ini_filepath']
)
def test_cbrx_read_ini(section, ini_filepath, expectation):
    c = Configuration(section, ini_filepath)
    with expectation:
        c.read()


@pytest.mark.parametrize(
    'section, ini_filepath, expected',
    [
        ('hostA', INI, HOST_A),
        ('hostB', INI, HOST_B)
    ],
    indirect=['ini_filepath']
)
def test_cbrx_ini_items(section, ini_filepath, expected):
    c = Configuration(section, ini_filepath)
    c.read()
    assert expected == c.items()


@pytest.mark.parametrize(
    'section, ini_filepath, expected',
    [
        ('host', INI, pytest.raises(ConfigurationSectionError)),
        ('', INI, pytest.raises(ConfigurationSectionError)),
        (list(), INI, pytest.raises(ConfigurationSectionError))
    ],
    indirect=['ini_filepath'])
def test_cbrx_invalid_ini_section(section, ini_filepath, expected):
    c = Configuration(section, ini_filepath)
    c.read()
    with expected:
        c.items()
