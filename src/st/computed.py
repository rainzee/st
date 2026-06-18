from collections.abc import Callable

from st.runtime import (
    Dependency,
    EffectLike,
    pop_effect,
    push_effect,
    schedule_effect,
    track_dependency,
)


class Computed[T]:
    """Read-only state derived from reactive dependencies."""

    def __init__(self, function: Callable[[], T]) -> None:
        """Create a computed value from a pure derivation function."""

        self._function = function
        self._effects: set[EffectLike] = set()
        self._dependencies: set[Dependency] = set()
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
        if not self._effects:
            return

        if self._recompute():
            for effect in self._effects.copy():
                schedule_effect(effect)

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
        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()

        push_effect(self)
        try:
            value = self._function()
        finally:
            pop_effect()

        self._dirty = False
        if self._initialized and value == self._value:
            return False

        self._value = value
        self._initialized = True
        return True

    def _depend_on(self, dependency: Dependency) -> None:
        if dependency in self._dependencies:
            return

        self._dependencies.add(dependency)
        dependency._subscribe(self)

    def _subscribe(self, effect: EffectLike) -> None:
        if self._disposed:
            return

        self._effects.add(effect)

    def _unsubscribe(self, effect: EffectLike) -> None:
        self._effects.discard(effect)

    def _dispose(self) -> None:
        if self._disposed:
            return

        self._disposed = True
        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()
        self._effects.clear()


def computed[T](function: Callable[[], T]) -> Computed[T]:
    """Create a read-only derived state."""

    return Computed(function)
