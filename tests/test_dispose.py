from st import State, computed, dispose, effect


def test_dispose_stops_effect_updates() -> None:
    state = State(1)
    values: list[int] = []
    effect_ = effect(lambda: values.append(state.value))

    dispose(effect_)
    state.value = 2

    assert values == [1]


def test_dispose_effect_is_idempotent() -> None:
    state = State(1)
    values: list[int] = []
    effect_ = effect(lambda: values.append(state.value))

    dispose(effect_)
    dispose(effect_)
    state.value = 2

    assert values == [1]


def test_dispose_stops_computed_recomputation() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)

    dispose(double)
    count.value = 2

    assert double.value == 2


def test_disposed_computed_is_not_tracked_by_new_effects() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[int] = []

    dispose(double)
    effect(lambda: values.append(double.value))
    count.value = 2

    assert values == [2]
