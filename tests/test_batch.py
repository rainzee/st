import pytest

from st import State, batch, computed, effect


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


def _set_and_return[T](state: State[T], value: T, result: object) -> object:
    state.value = value
    return result
