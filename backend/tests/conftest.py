import pytest

from backend.devices import reset_devices


@pytest.fixture(autouse=True)
def fresh_devices():
    reset_devices()
    yield
    reset_devices()
