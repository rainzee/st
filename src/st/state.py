from st.runtime import EffectLike, track_dependency


class State[T]:
    """Mutable reactive state."""

    def __init__(self, value: T) -> None:
        """Create state with an initial value."""

        self._value = value
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
        if value == self._value:
            return

        self._value = value
        for effect in self._effects.copy():
            effect()

    def _subscribe(self, effect: EffectLike) -> None:
        self._effects.add(effect)

    def _unsubscribe(self, effect: EffectLike) -> None:
        self._effects.discard(effect)
