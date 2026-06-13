from st import State


def test_state_exposes_initial_value(state: State[int]) -> None:
    assert state.value == 1


def test_state_updates_value(state: State[int]) -> None:
    state.value = 2

    assert state.value == 2


def test_state_can_store_none() -> None:
    state = State[str | None]("ready")

    state.value = None

    assert state.value is None
