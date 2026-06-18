import pytest

from st import State, computed, effect, peek, readonly


def test_readonly_exposes_current_state_value() -> None:
    count = State(1)
    view = readonly(count)

    assert view.value == 1

    count.value = 2

    assert view.value == 2


def test_readonly_value_cannot_be_assigned() -> None:
    count = State(1)
    view = readonly(count)

    with pytest.raises(AttributeError):
        view.value = 2

    assert count.value == 1


def test_readonly_tracks_underlying_state_dependency() -> None:
    count = State(1)
    view = readonly(count)
    values: list[int] = []

    effect(lambda: values.append(view.value))
    count.value = 2

    assert values == [1, 2]


def test_readonly_peek_reads_without_tracking_dependency() -> None:
    count = State(1)
    view = readonly(count)
    values: list[int] = []

    effect(lambda: values.append(peek(view)))
    count.value = 2

    assert values == [1]
    assert peek(view) == 2


def test_readonly_wraps_computed_value() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    view = readonly(double)

    assert view.value == 2

    count.value = 2

    assert view.value == 4
