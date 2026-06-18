from st import State, computed, effect


def test_computed_derives_value_from_state() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)

    count.value = 2

    assert double.value == 4


def test_computed_can_depend_on_another_computed() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    message = computed(lambda: f"double={double.value}")

    count.value = 2

    assert message.value == "double=4"


def test_computed_does_not_run_before_it_is_read() -> None:
    count = State(1)
    calls: list[int] = []

    double = computed(lambda: calls.append(count.value) or count.value * 2)

    assert calls == []
    assert double.value == 2
    assert calls == [1]


def test_unread_computed_does_not_subscribe_to_dependencies() -> None:
    count = State(1)
    calls: list[int] = []

    double = computed(lambda: calls.append(count.value) or count.value * 2)
    count.value = 2

    assert calls == []
    assert double.value == 4
    assert calls == [2]


def test_computed_caches_value_until_dependency_changes() -> None:
    count = State(1)
    calls: list[int] = []
    double = computed(lambda: calls.append(count.value) or count.value * 2)

    assert double.value == 2
    assert double.value == 2
    count.value = 2
    assert calls == [1]
    assert double.value == 4

    assert calls == [1, 2]


def test_computed_does_not_notify_dependents_when_value_is_unchanged() -> None:
    count = State(1)
    parity = computed(lambda: count.value % 2)
    values: list[int] = []
    effect(lambda: values.append(parity.value))

    count.value = 3

    assert values == [1]
