import pytest

from st import State, batch, computed, dispose, effect


def test_batch_defers_effect_until_callback_completes() -> None:
    state = State(1)
    values: list[int] = []
    effect(lambda: values.append(state.value))

    result = batch(lambda: _set_and_return(state, 2, "done"))

    assert result == "done"
    assert values == [1, 2]


def test_batch_context_defers_effect_until_block_completes() -> None:
    state = State(1)
    values: list[int] = []
    effect(lambda: values.append(state.value))

    with batch():
        state.value = 2
        assert values == [1]

    assert values == [1, 2]


def test_batch_coalesces_multiple_updates_to_one_effect_run() -> None:
    state = State(1)
    values: list[int] = []
    effect(lambda: values.append(state.value))

    def update() -> None:
        state.value = 2
        state.value = 3

    batch(update)

    assert values == [1, 3]


def test_nested_batch_flushes_after_outer_batch_completes() -> None:
    state = State(1)
    values: list[int] = []
    effect(lambda: values.append(state.value))

    def update() -> None:
        state.value = 2
        with batch():
            state.value = 3
        assert values == [1]

    batch(update)

    assert values == [1, 3]


def test_batch_flushes_when_callback_raises() -> None:
    state = State(1)
    values: list[int] = []
    effect(lambda: values.append(state.value))

    def update() -> None:
        state.value = 2
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        batch(update)

    assert values == [1, 2]


def test_batch_context_flushes_when_block_raises() -> None:
    state = State(1)
    values: list[int] = []
    effect(lambda: values.append(state.value))

    with pytest.raises(RuntimeError, match="boom"):
        with batch():
            state.value = 2
            raise RuntimeError("boom")

    assert values == [1, 2]


def test_batch_updates_computed_before_dependent_effect_runs() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[tuple[int, int]] = []
    effect(lambda: values.append((count.value, double.value)))

    def update() -> None:
        count.value = 2
        count.value = 3

    batch(update)

    assert values == [(1, 2), (3, 6)]


def test_batch_preserves_effect_order_within_same_priority() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[str] = []

    effect(lambda: values.append(f"first {count.value}"))
    effect(lambda: values.append(f"second {count.value}"))
    effect(lambda: values.append(f"double {double.value}"))
    values.clear()

    with batch():
        count.value = 2

    assert values == ["first 2", "second 2", "double 4"]


def test_batch_flushes_computations_scheduled_during_flush() -> None:
    first = State(0)
    second = State(0)
    values: list[str] = []

    def copy_first_to_second() -> None:
        value = first.value
        values.append(f"first {value}")
        if value:
            second.value = value

    effect(copy_first_to_second)
    effect(lambda: values.append(f"second {second.value}"))
    values.clear()

    with batch():
        first.value = 1

    assert values == ["first 1", "second 1"]


def test_batch_drops_pending_effect_that_is_disposed_before_flush() -> None:
    count = State(1)
    values: list[int] = []
    effect_ = effect(lambda: values.append(count.value))

    with batch():
        count.value = 2
        dispose(effect_)

    assert values == [1]


def test_batch_recomputes_computed_once_for_multiple_source_updates() -> None:
    first = State(1)
    second = State(10)
    calls: list[tuple[int, int]] = []
    total = computed(lambda: calls.append((first.value, second.value)) or first.value + second.value)
    values: list[int] = []
    effect(lambda: values.append(total.value))
    calls.clear()
    values.clear()

    with batch():
        first.value = 2
        second.value = 20

    assert calls == [(2, 20)]
    assert values == [22]


def _set_and_return[T](state: State[T], value: T, result: object) -> object:
    state.value = value
    return result
