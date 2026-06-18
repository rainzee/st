from st import State, effect, state


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


def test_state_supports_custom_equality() -> None:
    count = state(1, equals=lambda old, new: old % 2 == new % 2)
    values: list[int] = []
    effect(lambda: values.append(count.value))

    count.value = 3
    count.value = 4

    assert values == [1, 4]
    assert count.value == 4


def test_state_equals_false_always_notifies() -> None:
    count = state(1, equals=False)
    values: list[int] = []
    effect(lambda: values.append(count.value))

    count.value = 1

    assert values == [1, 1]


def test_state_notifies_effects_in_subscription_order() -> None:
    count = state(1)
    values: list[str] = []

    effect(lambda: values.append(f"first {count.value}"))
    effect(lambda: values.append(f"second {count.value}"))
    values.clear()

    count.value = 2

    assert values == ["first 2", "second 2"]


def test_state_class_accepts_custom_equality() -> None:
    count = State(1, equals=lambda old, new: old % 2 == new % 2)
    values: list[int] = []
    effect(lambda: values.append(count.value))

    count.value = 3
    count.value = 4

    assert values == [1, 4]
