import pytest
import serial_mock


@pytest.fixture(scope='session')
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope='session')
def dummy_serial():
    def create_dummy_serial(test_class):
        return serial_mock.DummySerial(test_class)
    return create_dummy_serial
