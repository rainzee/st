from st import State, computed


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
