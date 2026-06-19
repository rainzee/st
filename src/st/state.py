from collections.abc import Callable
from typing import Literal

from st.protocols import Computation
from st.runtime import schedule_computation, track_source

type Equality[T] = Callable[[T, T], bool] | Literal[False]


def _default_equals[T](old: T, new: T) -> bool:
    return old == new


class State[T]:
    """Mutable reactive state."""

    def __init__(self, value: T, *, equals: Equality[T] = _default_equals) -> None:
        """Create state with an initial value."""

        self._value = value
        self._equals = equals if equals else None
        self._subscribers: dict[Computation, None] = {}

    @property
    def value(self) -> T:
        """Current value.

        Reads are tracked when an effect or computed value is active.
        Writes notify subscribed computations when the value changes.
        """

        track_source(self)
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        if self._equals is not None and self._equals(self._value, value):
            return

        self._value = value

        for computation in list(self._subscribers):
            schedule_computation(computation)

    def _subscribe(self, computation: Computation) -> None:
        self._subscribers[computation] = None

    def _unsubscribe(self, computation: Computation) -> None:
        self._subscribers.pop(computation, None)

    def _peek(self) -> T:
        return self._value


def state[T](value: T, *, equals: Equality[T] = _default_equals) -> State[T]:
    """Create mutable reactive state."""

    return State(value, equals=equals)
