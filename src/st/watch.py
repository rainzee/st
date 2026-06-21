from collections.abc import Callable
from inspect import Parameter, signature
from typing import Literal, Protocol, TypeIs, cast, overload

from st.protocols import Cleanup, Source
from st.runtime import _pause_tracking, _restore_tracking, pop_computation, push_computation, run_cleanups
from st.scope import register_disposable

type WatchCleanup = Callable[[], None]
type WatchCleanupRegistrar = Callable[[WatchCleanup], None]
type WatchEquality[T] = Callable[[T, T], bool] | Literal[False]
_UNSET = object()


def _default_equals[T](old: T, new: T) -> bool:
    return old == new


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
        equals: WatchEquality[T] = _default_equals,
    ) -> None:
        self._source = source
        self._callback: WatchCallback[T] | None
        self._callback_with_cleanup: WatchCallbackWithCleanup[T] | None
        if _accepts_cleanup(callback):
            self._callback = None
            self._callback_with_cleanup = callback
        else:
            self._callback = callback
            self._callback_with_cleanup = None

        self._immediate = immediate
        self._equals = equals if equals else None
        self._sources: set[Source] = set()
        self._cleanups: list[Cleanup] = []
        self._disposed = False
        self._initialized = False
        self._value: T | object = _UNSET
        self._priority = 1

    def __call__(self) -> None:
        if self._disposed:
            return

        for source in self._sources:
            source._unsubscribe(self)

        self._sources.clear()

        push_computation(self)
        try:
            value = self._source()
        finally:
            pop_computation()

        if not self._initialized:
            self._initialized = True
            self._value = value

            if self._immediate:
                self._run_callback(value, None)

            return

        old = cast(T, self._value)
        if self._equals is not None and self._equals(old, value):
            return

        self._run_callback(value, old)
        self._value = value

    def _depend_on(self, source: Source) -> None:
        if source in self._sources:
            return

        self._sources.add(source)
        source._subscribe(self)

    def _add_cleanup(self, cleanup: Cleanup) -> None:
        if self._disposed:
            cleanup()
            return

        self._cleanups.append(cleanup)

    def _run_callback(self, value: T, old: T | None) -> None:
        self._run_cleanups()

        active_computations = _pause_tracking()

        try:
            callback_with_cleanup = self._callback_with_cleanup
            if callback_with_cleanup is not None:
                callback_with_cleanup(value, old, self._add_cleanup)
                return

            callback = self._callback
            if callback is not None:
                callback(value, old)
        finally:
            _restore_tracking(active_computations)

    def _run_cleanups(self) -> None:
        run_cleanups(self._cleanups)

    def dispose(self) -> None:
        """Stop this watcher from receiving future updates."""

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

        for source in self._sources:
            source._unsubscribe(self)

        self._sources.clear()

        if cleanup_error is not None:
            raise cleanup_error


@overload
def watch[T](
    source: Callable[[], T],
    callback: WatchCallback[T],
    *,
    immediate: bool = False,
    equals: WatchEquality[T] = _default_equals,
) -> Watch[T]: ...


@overload
def watch[T](
    source: Callable[[], T],
    callback: WatchCallbackWithCleanup[T],
    *,
    immediate: bool = False,
    equals: WatchEquality[T] = _default_equals,
) -> Watch[T]: ...


def watch[T](
    source: Callable[[], T],
    callback: WatchCallback[T] | WatchCallbackWithCleanup[T],
    *,
    immediate: bool = False,
    equals: WatchEquality[T] = _default_equals,
) -> Watch[T]:
    """Watch an explicit reactive source and call back with new and old values."""

    watcher = Watch(source, callback, immediate=immediate, equals=equals)
    register_disposable(watcher)

    try:
        watcher()
    except BaseException as error:
        try:
            watcher._dispose()
        except BaseException as cleanup_error:
            raise BaseExceptionGroup("watch failed and cleanup failed", [error, cleanup_error]) from error
        raise

    return watcher


def _accepts_cleanup[T](callback: WatchCallback[T] | WatchCallbackWithCleanup[T]) -> TypeIs[WatchCallbackWithCleanup[T]]:
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
