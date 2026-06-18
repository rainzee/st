import pytest

from st import State, computed, effect


def test_effect_tracks_state_dependency() -> None:
    state = State(1)
    values: list[int] = []

    effect(lambda: values.append(state.value))

    state.value = 2

    assert values == [1, 2]


def test_effect_disposes_initial_dependencies_when_initial_run_raises() -> None:
    state = State(1)
    values: list[int] = []

    def fail() -> None:
        values.append(state.value)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        effect(fail)

    state.value = 2

    assert values == [1]


def test_effect_replaces_stale_dependencies() -> None:
    enabled = State(True)
    first = State("first")
    second = State("second")
    values: list[str] = []

    def collect_value() -> None:
        if enabled.value:
            values.append(first.value)
            return

        values.append(second.value)

    effect(collect_value)

    enabled.value = False
    first.value = "ignored"
    second.value = "updated"

    assert values == ["first", "second", "updated"]


def test_effect_tracks_computed_dependency() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[int] = []

    effect(lambda: values.append(double.value))

    count.value = 2

    assert values == [2, 4]


def test_effect_does_not_recurse_when_it_updates_a_dependency() -> None:
    state = State(0)
    values: list[int] = []

    def increment_dependency() -> None:
        values.append(state.value)
        state.value += 1

    effect(increment_dependency)

    assert values == [0]
    assert state.value == 1


def test_effect_that_updates_a_dependency_still_responds_to_external_updates() -> None:
    state = State(0)
    values: list[int] = []

    def increment_dependency() -> None:
        values.append(state.value)
        state.value += 1

    effect(increment_dependency)
    state.value = 10

    assert values == [0, 10]
    assert state.value == 11
