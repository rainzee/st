from collections.abc import Callable

from st.protocols import Computation, Source
from st.runtime import (
    pop_computation,
    push_computation,
    schedule_computation,
    track_dependency,
)
from st.scope import register_disposable


class Computed[T]:
    """Read-only state derived from reactive dependencies."""

    def __init__(self, function: Callable[[], T]) -> None:
        """Create a computed value from a pure derivation function."""

        self._function = function
        self._subscribers: dict[Computation, None] = {}
        self._sources: set[Source] = set()
        self._initialized = False
        self._dirty = True
        self._value: T
        self._disposed = False
        self._priority = 0

    def __call__(self) -> None:
        """Mark this computed value dirty when a dependency changes."""

        if self._disposed:
            return

        self._dirty = True
        if not self._subscribers:
            return

        if self._recompute():
            for computation in list(self._subscribers):
                schedule_computation(computation)

    @property
    def value(self) -> T:
        """Current derived value.

        Reads are tracked when an effect or another computed value is active.
        """

        if not self._disposed:
            track_dependency(self)

        if self._dirty:
            self._recompute()

        return self._value

    def _peek(self) -> T:
        if self._dirty:
            self._recompute()

        return self._value

    def _recompute(self) -> bool:
        for source in self._sources:
            source._unsubscribe(self)

        self._sources.clear()
        push_computation(self)

        try:
            value = self._function()
        finally:
            pop_computation()

        self._dirty = False
        if self._initialized and value == self._value:
            return False

        self._value = value
        self._initialized = True
        return True

    def _depend_on(self, source: Source) -> None:
        if source in self._sources:
            return

        self._sources.add(source)
        source._subscribe(self)

    def _subscribe(self, computation: Computation) -> None:
        if self._disposed:
            return

        self._subscribers[computation] = None

    def _unsubscribe(self, computation: Computation) -> None:
        self._subscribers.pop(computation, None)

    def dispose(self) -> None:
        """Stop this computed value from receiving future updates."""

        self._dispose()

    def _dispose(self) -> None:
        if self._disposed:
            return

        self._disposed = True

        for source in self._sources:
            source._unsubscribe(self)

        self._sources.clear()
        self._subscribers.clear()


def computed[T](function: Callable[[], T]) -> Computed[T]:
    """Create a read-only derived state."""

    computed_ = Computed(function)
    register_disposable(computed_)
    return computed_
