from collections.abc import Callable

from st.runtime import Cleanup, Dependency, pop_effect, push_effect
from st.scope import register_disposable


class Effect:
    """Reactive side effect with automatic dependency tracking."""

    def __init__(self, function: Callable[[], None]) -> None:
        """Create an effect wrapper without running it."""

        self._function = function
        self._cleanups: list[Cleanup] = []
        self._dependencies: set[Dependency] = set()
        self._disposed = False
        self._priority = 1

    def __call__(self) -> None:
        """Run the effect and replace its tracked dependencies."""

        if self._disposed:
            return

        self._run_cleanups()

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

    def _add_cleanup(self, cleanup: Cleanup) -> None:
        if self._disposed:
            cleanup()
            return

        self._cleanups.append(cleanup)

    def _run_cleanups(self) -> None:
        exception: BaseException | None = None

        while self._cleanups:
            cleanup = self._cleanups.pop()
            try:
                cleanup()
            except BaseException as error:
                if exception is None:
                    exception = error

        if exception is not None:
            raise exception

    def dispose(self) -> None:
        """Stop this effect from receiving future updates."""

        self._dispose()

    def _dispose(self) -> None:
        if self._disposed:
            return

        self._disposed = True
        self._run_cleanups()
        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()


def effect(function: Callable[[], None]) -> Effect:
    """Create and immediately run a reactive side effect."""

    effect_ = Effect(function)
    register_disposable(effect_)
    try:
        effect_()
    except BaseException:
        effect_._dispose()
        raise

    return effect_
