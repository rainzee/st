from collections.abc import Callable

from st.effect import Effect
from st.runtime import EffectLike, track_dependency


class Computed[T]:
    """Read-only state derived from reactive dependencies."""

    def __init__(self, function: Callable[[], T]) -> None:
        """Create a computed value from a pure derivation function."""

        self._function = function
        self._effects: set[EffectLike] = set()
        self._initialized = False
        self._value: T
        self._effect = Effect(self._recompute)
        self._effect()

    @property
    def value(self) -> T:
        """Current derived value.

        Reads are tracked when an effect or another computed value is active.
        """

        track_dependency(self)
        return self._value

    def _peek(self) -> T:
        return self._value

    def _recompute(self) -> None:
        value = self._function()
        if self._initialized and value == self._value:
            return

        self._value = value
        self._initialized = True
        for effect in self._effects.copy():
            effect()

    def _subscribe(self, effect: EffectLike) -> None:
        self._effects.add(effect)

    def _unsubscribe(self, effect: EffectLike) -> None:
        self._effects.discard(effect)


def computed[T](function: Callable[[], T]) -> Computed[T]:
    """Create a read-only derived state."""

    return Computed(function)
