from collections.abc import Callable
from typing import Literal

from st.runtime import EffectLike, schedule_effect, track_dependency


type Equality[T] = Callable[[T, T], bool] | Literal[False]


def _default_equals[T](old: T, new: T) -> bool:
    return old == new


class State[T]:
    """Mutable reactive state."""

    def __init__(self, value: T, *, equals: Equality[T] = _default_equals) -> None:
        """Create state with an initial value."""

        self._value = value
        self._equals = equals
        self._effects: set[EffectLike] = set()

    @property
    def value(self) -> T:
        """Current value.

        Reads are tracked when an effect or computed value is active.
        Writes notify dependents when the value changes.
        """

        track_dependency(self)
        return self._value

    def _peek(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        if self._equals is not False and self._equals(self._value, value):
            return

        self._value = value
        for effect in self._effects.copy():
            schedule_effect(effect)

    def _subscribe(self, effect: EffectLike) -> None:
        self._effects.add(effect)

    def _unsubscribe(self, effect: EffectLike) -> None:
        self._effects.discard(effect)


def state[T](value: T, *, equals: Equality[T] = _default_equals) -> State[T]:
    """Create mutable reactive state."""

    return State(value, equals=equals)
