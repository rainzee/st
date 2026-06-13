from st import State, computed, effect, peek


def test_state_exposes_initial_value(state: State[int]) -> None:
    assert state.value == 1


def test_state_updates_value(state: State[int]) -> None:
    state.value = 2

    assert state.value == 2


def test_state_can_store_none() -> None:
    state = State[str | None]("ready")

    state.value = None

    assert state.value is None


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


def test_computed_derives_value_from_state() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)

    count.value = 2

    assert double.value == 4


def test_effect_tracks_computed_dependency() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[int] = []

    effect(lambda: values.append(double.value))

    count.value = 2

    assert values == [2, 4]


def test_computed_can_depend_on_another_computed() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    message = computed(lambda: f"double={double.value}")

    count.value = 2

    assert message.value == "double=4"


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
