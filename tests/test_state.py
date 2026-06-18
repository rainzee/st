from st import State, state


def test_state_exposes_initial_value(state: State[int]) -> None:
    assert state.value == 1


def test_state_updates_value(state: State[int]) -> None:
    state.value = 2

    assert state.value == 2


def test_state_can_store_none() -> None:
    state = State[str | None]("ready")

    state.value = None

    assert state.value is None


def test_state_factory_creates_state() -> None:
    count = state(1)

    assert isinstance(count, State)
    assert count.value == 1
