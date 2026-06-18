from collections.abc import Callable
from typing import Protocol


class Dependency(Protocol):
    def _subscribe(self, effect: "EffectLike") -> None: ...

    def _unsubscribe(self, effect: "EffectLike") -> None: ...


class EffectLike(Protocol):
    def __call__(self) -> None: ...

    def _depend_on(self, dependency: Dependency) -> None: ...


class Peekable[T](Protocol):
    def _peek(self) -> T: ...


class Disposable(Protocol):
    def _dispose(self) -> None: ...


type Cleanup = Callable[[], None]


_active_effects: list[EffectLike] = []
_active_scopes: list["Scope"] = []
_batch_depth = 0
_pending_effects: set[EffectLike] = set()
_is_flushing = False


class Scope:
    """Owner scope for reactive resources and cleanup callbacks."""

    def __init__(self) -> None:
        self._cleanups: list[Cleanup] = []
        self._disposed = False

        if _active_scopes:
            _active_scopes[-1]._add_cleanup(self._dispose)

    def __enter__(self) -> "Scope":
        if self._disposed:
            raise RuntimeError("Cannot enter a disposed scope")

        _active_scopes.append(self)
        return self

    def __exit__(self, *args: object) -> None:
        _active_scopes.pop()
        self._dispose()

    def dispose(self) -> None:
        """Dispose this scope and run its cleanup callbacks."""

        self._dispose()

    def _add_cleanup(self, cleanup: Cleanup) -> None:
        if self._disposed:
            cleanup()
            return

        self._cleanups.append(cleanup)

    def _dispose(self) -> None:
        if self._disposed:
            return

        self._disposed = True
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


class _UntrackContext:
    def __init__(self) -> None:
        self._active_effects: list[EffectLike] = []

    def __enter__(self) -> None:
        self._active_effects = _active_effects.copy()
        _active_effects.clear()

    def __exit__(self, *args: object) -> None:
        _active_effects[:] = self._active_effects


class _BatchContext:
    def __enter__(self) -> None:
        _begin_batch()

    def __exit__(self, *args: object) -> None:
        _end_batch()


def track_dependency(dependency: Dependency) -> None:
    if _active_effects:
        _active_effects[-1]._depend_on(dependency)


def push_effect(effect: EffectLike) -> None:
    _active_effects.append(effect)


def pop_effect() -> None:
    _active_effects.pop()


def register_cleanup(cleanup: Cleanup) -> None:
    if not _active_scopes:
        raise RuntimeError("on_cleanup() requires an active scope")

    _active_scopes[-1]._add_cleanup(cleanup)


def register_disposable(disposable: Disposable) -> None:
    if _active_scopes:
        _active_scopes[-1]._add_cleanup(disposable._dispose)


def schedule_effect(effect: EffectLike) -> None:
    if effect in _active_effects:
        return

    if _batch_depth > 0 or _is_flushing:
        _pending_effects.add(effect)
        return

    effect()


def _flush_effects() -> None:
    global _is_flushing

    if _is_flushing:
        return

    _is_flushing = True
    try:
        while _pending_effects:
            effect = min(_pending_effects, key=lambda item: getattr(item, "_priority", 1))
            _pending_effects.remove(effect)
            effect()
    finally:
        _is_flushing = False


def _begin_batch() -> None:
    global _batch_depth

    _batch_depth += 1


def _end_batch() -> None:
    global _batch_depth

    _batch_depth -= 1
    if _batch_depth == 0:
        _flush_effects()


def peek[T](value: Peekable[T]) -> T:
    """Read a reactive value without tracking it as a dependency."""

    return value._peek()


def untrack[T](function: Callable[[], T] | None = None) -> T | _UntrackContext:
    """Disable dependency tracking for a function or context block."""

    context = _UntrackContext()
    if function is None:
        return context

    with context:
        return function()


def batch[T](function: Callable[[], T] | None = None) -> T | _BatchContext:
    """Defer reactive updates for a function or context block."""

    context = _BatchContext()
    if function is None:
        return context

    with context:
        return function()


def scope() -> Scope:
    """Create an owner scope for reactive resources."""

    return Scope()


def on_cleanup(cleanup: Cleanup) -> None:
    """Register a cleanup callback on the current scope."""

    register_cleanup(cleanup)


def dispose(value: Disposable) -> None:
    """Stop a reactive value from receiving future updates."""

    value._dispose()
