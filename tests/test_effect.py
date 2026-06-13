from st import State, computed, effect


def test_effect_tracks_state_dependency() -> None:
    state = State(1)
    values: list[int] = []

    effect(lambda: values.append(state.value))

    state.value = 2

    assert values == [1, 2]


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
