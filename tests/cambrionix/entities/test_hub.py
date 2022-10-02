""" Unit tests on Cambrionix hub entity """

import pytest
from contextlib import contextmanager
from cambrionix.entities.hub import UsbHub, PortFlags, Port, PortList


@pytest.fixture
def portlist():
    return PortList()


@pytest.fixture(scope='module')
def portflags():
    return PortFlags('O', 'D')


@pytest.fixture(scope='module')
def port(index=1):
    return Port(index)


@pytest.fixture
def usb_hub():
    return UsbHub()


@contextmanager
def does_not_raise():
    yield


@pytest.mark.parametrize('flag, expectation', [
    ('', does_not_raise()), ('T', does_not_raise()),
    ('E', does_not_raise()), ('R', does_not_raise()),
    ('r', does_not_raise()), ('e', pytest.raises(ValueError)),
    ('r r', pytest.raises(ValueError)), ('ET', does_not_raise()),
    ('rER', does_not_raise()), ('BER', pytest.raises(ValueError)),
    (['T', 'r', 'E', 'R'], does_not_raise()), (('E', 'R'), does_not_raise())
])
def test_system_portflag(portflags, flag, expectation):
    with expectation:
        setattr(portflags, 'system', flag)


@pytest.mark.parametrize('flag, expectation', [
    ('A', does_not_raise()), ('D', does_not_raise()),
    ('Attached', pytest.raises(ValueError)),
    ('Dd', pytest.raises(ValueError))
])
def test_state_portflag(portflags, flag, expectation):
    with expectation:
        setattr(portflags, 'state', flag)


@pytest.mark.parametrize('flag, expectation', [
    ('S', does_not_raise()), ('O', does_not_raise()),
    ('B', does_not_raise()), ('OO', pytest.raises(ValueError)),
    ('P', does_not_raise()), ('I', does_not_raise()),
    ('C', does_not_raise()), ('F', does_not_raise()),
    ('T', pytest.raises(ValueError)), ('Ff', pytest.raises(ValueError))
])
def test_mode_portflag(portflags, flag, expectation):
    with expectation:
        setattr(portflags, 'mode', flag)


@pytest.mark.parametrize('first, second, expectation', [
    (PortFlags('S', 'A', 'R'), PortFlags('S', 'A', 'R'), does_not_raise()),
    (PortFlags('O', 'D'), PortFlags('S', 'A'), pytest.raises(AssertionError))
])
def test_portflag_equality(first, second, expectation):
    with expectation:
        assert first == second


@pytest.mark.parametrize('first, second, expectation', [
    (PortFlags('S', 'A', 'R', 'E'), PortFlags('S', 'A', 'R', 'E'), pytest.raises(AssertionError)),
    (PortFlags('O', 'D'), PortFlags('S', 'A'), does_not_raise())
])
def test_portflag_inequality(first, second, expectation):
    with expectation:
        assert first != second


@pytest.mark.parametrize('index, expectation', [
    (2, does_not_raise()),
    ('2', does_not_raise()),
    (-1, pytest.raises(ValueError)),
    (list(), pytest.raises(ValueError))
])
def test_port_index(index, expectation):
    with expectation:
        Port(index)


@pytest.mark.parametrize('ma, expectation', [
    ('1000', does_not_raise()),
    (100, does_not_raise()),
    (0, does_not_raise()),
    (dict(), pytest.raises(ValueError)),
    ('test', pytest.raises(ValueError))
])
def test_port_current_ma(port, ma, expectation):
    with expectation:
        setattr(port, 'current_ma', ma)


@pytest.mark.parametrize('flags, expectation', [
    (None, does_not_raise()),
    (PortFlags('C', 'A'), does_not_raise()),
    (list(), pytest.raises(ValueError)),
    ('str', pytest.raises(ValueError))
])
def test_port_flags(port, flags, expectation):
    with expectation:
        setattr(port, 'flags', flags)


@pytest.mark.parametrize('id, expectation', [
    (1, does_not_raise()),
    ('2', does_not_raise()),
    (list(), pytest.raises(ValueError)),
    (-3, pytest.raises(ValueError))
])
def test_port_profile_id(port, id, expectation):
    with expectation:
        setattr(port, 'profile_id', id)


@pytest.mark.parametrize('seconds, expectation', [
    (20, does_not_raise()),
    ('5.0', pytest.raises(ValueError)),
    (20.0, does_not_raise()),
    (list(), pytest.raises(ValueError)),
    (-100, pytest.raises(ValueError))
])
def test_port_time_charging(port, seconds, expectation):
    with expectation:
        setattr(port, 'time_charging', seconds)


@pytest.mark.parametrize('seconds, expectation', [
    (20, does_not_raise()),
    ('x', does_not_raise()),
    ('5.0', pytest.raises(ValueError)),
    (20.0, does_not_raise()),
    (list(), pytest.raises(ValueError)),
    (-1000, pytest.raises(ValueError))
])
def test_port_time_charged(port, seconds, expectation):
    with expectation:
        setattr(port, 'time_charged', seconds)


@pytest.mark.parametrize('energy, expectation', [
    (1, does_not_raise()),
    ('x', pytest.raises(ValueError)),
    ('0.05', does_not_raise()),
    (0.01, does_not_raise()),
    (list(), pytest.raises(ValueError)),
    (-1000, pytest.raises(ValueError))
])
def test_port_energy(port, energy, expectation):
    with expectation:
        setattr(port, 'energy', energy)


@pytest.mark.parametrize('first, second, expectation', [
    (Port(1, energy=0.01), Port(1, energy=0.02), does_not_raise()),
    (Port(2, profile_id=1), Port(3, profile_id=1), pytest.raises(AssertionError)),
    (Port(3), list(), pytest.raises(AssertionError))
])
def test_port_equality(first, second, expectation):
    with expectation:
        assert first == second


@pytest.mark.parametrize('first, second, expectation', [
    (Port(2), Port('1', energy=0.02), does_not_raise()),
    (Port('3', profile_id=1), Port(3, profile_id=1), pytest.raises(AssertionError)),
    (Port('4'), dict(), does_not_raise())
])
def test_port_inequality(first, second, expectation):
    with expectation:
        assert first != second


@pytest.mark.parametrize('index, attributes', [
    (5, {'energy': 0.02, 'current_ma': 1, 'profile_id': 5}),
    ('8', {'energy': 0.01, 'current_ma': 1, 'profile_id': 5})
])
def test_search_portlist_by_index(portlist, index, attributes):
    expected = Port(index, **attributes)
    portlist.append(expected)
    actual = portlist.search_by_index(index)
    assert expected == actual


@pytest.mark.parametrize('index', [list(), dict(), 'A'])
def test_search_portlist_by_invalid_index(portlist, index):
    with pytest.raises(ValueError):
        portlist.search_by_index(index)


@pytest.mark.parametrize('index, flag, attributes', [
    (2, 'D', {'flags': PortFlags(state='D', mode='O')}),
    (4, 'S', {'flags': PortFlags(state='A', mode='S')})
])
def test_search_portlist_by_flag(portlist, index, flag, attributes):
    expected = Port(index, **attributes)
    portlist.append(expected)
    ports = portlist.search_by_flag(flag)
    assert expected in ports


def test_search_usb_port(usb_hub, index=1):
    p = Port(index)
    usb_hub.new_port(index)
    assert p == usb_hub.search_port(index)


def test_remove_port_from_usb(usb_hub, index=2):
    p = Port(index)
    usb_hub.new_port(index)
    assert p == usb_hub.remove_port(index)


def test_update_invalid_usb_port(usb_hub):
    with pytest.raises(IndexError):
        usb_hub.update_port(10)


@pytest.mark.parametrize('index, attributes', [
    (2, {'energy': 0.02, 'profile_id': 1, 'flags': PortFlags('S', 'A')})
])
def test_update_usb_port(usb_hub, index, attributes):
    expected = Port(index, **attributes)
    usb_hub.new_port(index)
    usb_hub.update_port(index, **attributes)
    actual = usb_hub.search_port(index)
    for attr, value in vars(expected).items():
        assert value == getattr(actual, attr)
