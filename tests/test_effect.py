import pytest

from st import State, computed, effect, on_cleanup


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


def test_effect_runs_cleanup_before_next_run() -> None:
    state = State(1)
    values: list[str] = []

    def collect_value() -> None:
        value = state.value
        on_cleanup(lambda: values.append(f"cleanup {value}"))
        values.append(f"run {value}")

    effect(collect_value)
    state.value = 2

    assert values == ["run 1", "cleanup 1", "run 2"]


def test_effect_runs_cleanup_when_disposed() -> None:
    state = State(1)
    values: list[str] = []

    effect_ = effect(lambda: (on_cleanup(lambda: values.append("cleanup")), state.value))

    effect_.dispose()
    state.value = 2

    assert values == ["cleanup"]


def test_effect_runs_all_cleanups_when_cleanup_raises() -> None:
    state = State(1)
    values: list[str] = []

    def collect_value() -> None:
        state.value

        def first() -> None:
            values.append("first")
            raise RuntimeError("first")

        def second() -> None:
            values.append("second")
            raise RuntimeError("second")

        on_cleanup(first)
        on_cleanup(second)

    effect(collect_value)

    with pytest.raises(BaseExceptionGroup) as error:
        state.value = 2

    assert values == ["second", "first"]
    assert len(error.value.exceptions) == 2


def test_effect_unsubscribes_old_dependencies_when_cleanup_raises() -> None:
    state = State(1)
    values: list[int] = []

    def fail_cleanup() -> None:
        raise RuntimeError("cleanup")

    def collect_value() -> None:
        values.append(state.value)
        on_cleanup(fail_cleanup)

    effect(collect_value)

    with pytest.raises(RuntimeError, match="cleanup"):
        state.value = 2

    state.value = 3

    assert values == [1]


def test_effect_dispose_unsubscribes_dependencies_when_cleanup_raises() -> None:
    state = State(1)
    values: list[int] = []

    def fail_cleanup() -> None:
        raise RuntimeError("cleanup")

    def collect_value() -> None:
        values.append(state.value)
        on_cleanup(fail_cleanup)

    effect_ = effect(collect_value)

    with pytest.raises(RuntimeError, match="cleanup"):
        effect_.dispose()

    state.value = 2

    assert values == [1]


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
