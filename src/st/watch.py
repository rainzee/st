from collections.abc import Callable
from inspect import Parameter, signature
from typing import Protocol, cast, overload

from st.runtime import Cleanup, Dependency, _pause_tracking, _restore_tracking, pop_effect, push_effect
from st.scope import register_disposable


type WatchCleanup = Callable[[], None]
type WatchCleanupRegistrar = Callable[[WatchCleanup], None]
_UNSET = object()


class WatchCallback[T](Protocol):
    def __call__(self, new: T, old: T | None) -> None: ...


class WatchCallbackWithCleanup[T](Protocol):
    def __call__(self, new: T, old: T | None, on_cleanup: WatchCleanupRegistrar) -> None: ...


class Watch[T]:
    """Reactive watcher with an explicit source and old/new callback values."""

    def __init__(
        self,
        source: Callable[[], T],
        callback: WatchCallback[T] | WatchCallbackWithCleanup[T],
        *,
        immediate: bool = False,
    ) -> None:
        self._source = source
        self._callback = callback
        self._immediate = immediate
        self._dependencies: set[Dependency] = set()
        self._cleanups: list[Cleanup] = []
        self._disposed = False
        self._initialized = False
        self._value: T | object = _UNSET
        self._passes_cleanup = _accepts_cleanup(callback)
        self._priority = 1

    def __call__(self) -> None:
        if self._disposed:
            return

        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()

        push_effect(self)
        try:
            value = self._source()
        finally:
            pop_effect()

        if not self._initialized:
            self._initialized = True
            self._value = value
            if self._immediate:
                self._run_callback(value, None)
            return

        old = cast(T, self._value)
        if value == old:
            return

        self._value = value
        self._run_callback(value, old)

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

    def _run_callback(self, value: T, old: T | None) -> None:
        self._run_cleanups()

        active_effects = _pause_tracking()
        try:
            if self._passes_cleanup:
                callback = self._callback
                callback(value, old, self._add_cleanup)  # type: ignore[misc]
            else:
                callback = self._callback
                callback(value, old)  # type: ignore[misc]
        finally:
            _restore_tracking(active_effects)

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
        """Stop this watcher from receiving future updates."""

        self._dispose()

    def _dispose(self) -> None:
        if self._disposed:
            return

        self._disposed = True
        self._run_cleanups()
        for dependency in self._dependencies:
            dependency._unsubscribe(self)
        self._dependencies.clear()


@overload
def watch[T](source: Callable[[], T], callback: WatchCallback[T], *, immediate: bool = False) -> Watch[T]: ...


@overload
def watch[T](source: Callable[[], T], callback: WatchCallbackWithCleanup[T], *, immediate: bool = False) -> Watch[T]: ...


def watch[T](
    source: Callable[[], T],
    callback: WatchCallback[T] | WatchCallbackWithCleanup[T],
    *,
    immediate: bool = False,
) -> Watch[T]:
    """Watch an explicit reactive source and call back with new and old values."""

    watcher = Watch(source, callback, immediate=immediate)
    register_disposable(watcher)
    try:
        watcher()
    except BaseException:
        watcher._dispose()
        raise

    return watcher


def _accepts_cleanup(callback: Callable[..., object]) -> bool:
    try:
        parameters = signature(callback).parameters.values()
    except (TypeError, ValueError):
        return False

    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    return any(parameter.kind == Parameter.VAR_POSITIONAL for parameter in parameters) or len(positional) >= 3
