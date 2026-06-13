from st import State, computed, effect, peek


def test_peek_reads_state_without_tracking_dependency() -> None:
    state = State(1)
    values: list[int] = []

    effect(lambda: values.append(peek(state)))

    state.value = 2

    assert values == [1]


def test_peek_reads_computed_without_tracking_dependency() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[int] = []

    effect(lambda: values.append(peek(double)))

    count.value = 2

    assert values == [2]
    assert peek(double) == 4
