from collections.abc import Callable

from st.runtime import Dependency, pop_effect, push_effect


class Effect:
    """Reactive side effect with automatic dependency tracking."""

    def __init__(self, function: Callable[[], None]) -> None:
        """Create an effect wrapper without running it."""

        self._function = function
        self._dependencies: set[Dependency] = set()

    def __call__(self) -> None:
        """Run the effect and replace its tracked dependencies."""

        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()

        push_effect(self)
        try:
            self._function()
        finally:
            pop_effect()

    def _depend_on(self, dependency: Dependency) -> None:
        if dependency in self._dependencies:
            return

        self._dependencies.add(dependency)
        dependency._subscribe(self)


def effect(function: Callable[[], None]) -> Effect:
    """Create and immediately run a reactive side effect."""

    effect_ = Effect(function)
    effect_()
    return effect_
