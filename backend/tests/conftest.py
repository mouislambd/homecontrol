import os

os.environ.pop("DATABASE_URL", None)
os.environ.pop("TEST_DATABASE_URL", None)

import pytest

from backend.container import reset_state


@pytest.fixture(autouse=True)
def fresh_devices():
    reset_state()
    yield
    reset_state()
