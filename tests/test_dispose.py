import gc
import weakref

from st import State, computed, dispose, effect


def test_dispose_stops_effect_updates() -> None:
    state = State(1)
    values: list[int] = []
    effect_ = effect(lambda: values.append(state.value))

    dispose(effect_)
    state.value = 2

    assert values == [1]


def test_effect_dispose_method_stops_updates() -> None:
    state = State(1)
    values: list[int] = []
    effect_ = effect(lambda: values.append(state.value))

    effect_.dispose()
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


def test_effect_is_kept_alive_by_dependency_until_disposed() -> None:
    state = State(1)
    effect_ = effect(lambda: state.value)
    effect_ref = weakref.ref(effect_)

    del effect_
    gc.collect()

    assert effect_ref() is not None


def test_dispose_allows_effect_to_be_collected_while_dependency_lives() -> None:
    state = State(1)
    effect_ = effect(lambda: state.value)
    effect_ref = weakref.ref(effect_)

    dispose(effect_)
    del effect_
    gc.collect()

    assert effect_ref() is None


def test_unreachable_state_effect_cycle_is_collected() -> None:
    def create_cycle() -> tuple[weakref.ReferenceType[State[int]], weakref.ReferenceType]:
        state = State(1)
        effect_ = effect(lambda: state.value)
        return weakref.ref(state), weakref.ref(effect_)

    state_ref, effect_ref = create_cycle()
    gc.collect()

    assert state_ref() is None
    assert effect_ref() is None


def test_dispose_stops_computed_recomputation() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    assert double.value == 2

    dispose(double)
    count.value = 2

    assert double.value == 2


def test_computed_dispose_method_stops_recomputation() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    assert double.value == 2

    double.dispose()
    count.value = 2

    assert double.value == 2


def test_disposed_computed_is_not_tracked_by_new_effects() -> None:
    count = State(1)
    double = computed(lambda: count.value * 2)
    values: list[int] = []
    assert double.value == 2

    dispose(double)
    effect(lambda: values.append(double.value))
    count.value = 2

    assert values == [2]
