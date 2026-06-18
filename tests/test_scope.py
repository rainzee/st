import pytest

from st import State, computed, dispose, effect, on_cleanup, scope


def test_scope_disposes_effects_on_exit() -> None:
    count = State(1)
    values: list[int] = []

    with scope():
        effect(lambda: values.append(count.value))

    count.value = 2

    assert values == [1]


def test_scope_run_keeps_effects_alive_until_scope_is_disposed() -> None:
    count = State(1)
    values: list[int] = []
    owner = scope()

    owner.run(lambda: effect(lambda: values.append(count.value)))
    count.value = 2
    owner.dispose()
    count.value = 3

    assert values == [1, 2]


def test_scope_run_defers_cleanup_until_scope_is_disposed() -> None:
    values: list[str] = []
    owner = scope()

    owner.run(lambda: on_cleanup(lambda: values.append("cleanup")))

    assert values == []

    owner.dispose()

    assert values == ["cleanup"]


def test_scope_run_disposes_resources_when_setup_raises() -> None:
    count = State(1)
    values: list[int] = []
    owner = scope()

    def setup() -> None:
        effect(lambda: values.append(count.value))
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        owner.run(setup)

    count.value = 2

    assert values == [1]


def test_scope_disposes_effect_when_initial_run_raises() -> None:
    count = State(1)
    values: list[int] = []

    def fail() -> None:
        values.append(count.value)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        with scope():
            effect(fail)

    count.value = 2

    assert values == [1]


def test_scope_disposes_computed_values_on_exit() -> None:
    count = State(1)

    with scope():
        double = computed(lambda: count.value * 2)
        assert double.value == 2

    count.value = 2

    assert double.value == 2


def test_on_cleanup_runs_callbacks_when_scope_exits() -> None:
    values: list[str] = []

    with scope():
        on_cleanup(lambda: values.append("first"))
        on_cleanup(lambda: values.append("second"))

    assert values == ["second", "first"]


def test_on_cleanup_requires_active_scope() -> None:
    with pytest.raises(RuntimeError, match="active scope"):
        on_cleanup(lambda: None)


def test_dispose_scope_runs_registered_cleanups() -> None:
    values: list[str] = []

    with scope() as owner:
        on_cleanup(lambda: values.append("cleanup"))
        dispose(owner)

    assert values == ["cleanup"]


def test_scope_dispose_method_runs_registered_cleanups() -> None:
    values: list[str] = []

    with scope() as owner:
        on_cleanup(lambda: values.append("cleanup"))
        owner.dispose()

    assert values == ["cleanup"]


def test_nested_scope_is_disposed_with_parent_scope() -> None:
    count = State(1)
    values: list[int] = []

    with scope():
        with scope():
            effect(lambda: values.append(count.value))

    count.value = 2

    assert values == [1]
