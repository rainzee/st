from st import State, computed, effect, untrack


def test_untrack_reads_state_without_tracking_dependency() -> None:
    state = State(1)
    values: list[int] = []

    effect(lambda: values.append(untrack(lambda: state.value)))

    state.value = 2

    assert values == [1]


def test_untrack_context_reads_state_without_tracking_dependency() -> None:
    state = State(1)
    values: list[int] = []

    def collect() -> None:
        with untrack():
            value = state.value
        values.append(value)

    effect(collect)
    state.value = 2

    assert values == [1]


def test_untrack_returns_callback_value() -> None:
    state = State(1)

    value = untrack(lambda: state.value + 1)

    assert value == 2


def test_untrack_restores_tracking_after_callback() -> None:
    first = State(1)
    second = State(10)
    values: list[tuple[int, int]] = []

    effect(lambda: values.append((untrack(lambda: first.value), second.value)))

    first.value = 2
    second.value = 11

    assert values == [(1, 10), (2, 11)]


def test_untrack_context_restores_tracking_after_block() -> None:
    first = State(1)
    second = State(10)
    values: list[tuple[int, int]] = []

    def collect() -> None:
        with untrack():
            first_value = first.value
        values.append((first_value, second.value))

    effect(collect)
    first.value = 2
    second.value = 11

    assert values == [(1, 10), (2, 11)]


def test_untrack_reads_computed_without_tracking_dependency() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[int] = []

    effect(lambda: values.append(untrack(lambda: double.value)))

    count.value = 2

    assert values == [2]


def test_nested_effect_inside_untrack_still_tracks_its_dependencies() -> None:
    state = State(1)
    values: list[int] = []

    untrack(lambda: effect(lambda: values.append(state.value)))
    state.value = 2

    assert values == [1, 2]
