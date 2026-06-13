import pytest

from st import State


@pytest.fixture
def state() -> State[int]:
    return State(1)
