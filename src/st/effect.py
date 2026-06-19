from collections.abc import Callable

from st.protocols import Cleanup, Dependency
from st.runtime import pop_observer, push_observer, run_cleanups
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

        cleanup_error: BaseException | None = None
        try:
            self._run_cleanups()
        except BaseException as error:
            cleanup_error = error

        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()

        if cleanup_error is not None:
            raise cleanup_error

        push_observer(self)
        try:
            self._function()
        finally:
            pop_observer()

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
        run_cleanups(self._cleanups)

    def dispose(self) -> None:
        """Stop this effect from receiving future updates."""

        self._dispose()

    def _dispose(self) -> None:
        if self._disposed:
            return

        self._disposed = True
        cleanup_error: BaseException | None = None
        try:
            self._run_cleanups()
        except BaseException as error:
            cleanup_error = error

        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()

        if cleanup_error is not None:
            raise cleanup_error


def effect(function: Callable[[], None]) -> Effect:
    """Create and immediately run a reactive side effect."""

    effect_ = Effect(function)
    register_disposable(effect_)
    try:
        effect_()
    except BaseException as error:
        try:
            effect_._dispose()
        except BaseException as cleanup_error:
            raise BaseExceptionGroup("effect failed and cleanup failed", [error, cleanup_error]) from error

        raise

    return effect_
