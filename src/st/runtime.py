from collections.abc import Callable
from typing import Protocol


class Dependency(Protocol):
    def _subscribe(self, effect: "EffectLike") -> None: ...

    def _unsubscribe(self, effect: "EffectLike") -> None: ...


class EffectLike(Protocol):
    def __call__(self) -> None: ...

    def _depend_on(self, dependency: Dependency) -> None: ...

    def _add_cleanup(self, cleanup: "Cleanup") -> None: ...


class Peekable[T](Protocol):
    def _peek(self) -> T: ...


class Disposable(Protocol):
    def _dispose(self) -> None: ...


type Cleanup = Callable[[], None]


_active_effects: list[EffectLike] = []
_batch_depth = 0
_pending_effects: dict[EffectLike, None] = {}
_is_flushing = False


def run_cleanups(cleanups: list[Cleanup]) -> None:
    """Run cleanup callbacks in LIFO order and report any failures."""

    exceptions: list[BaseException] = []

    while cleanups:
        cleanup = cleanups.pop()
        try:
            cleanup()
        except BaseException as error:
            exceptions.append(error)

    if not exceptions:
        return

    if len(exceptions) == 1:
        raise exceptions[0]

    raise BaseExceptionGroup("cleanup callbacks failed", exceptions)


def track_dependency(dependency: Dependency) -> None:
    if _active_effects:
        _active_effects[-1]._depend_on(dependency)


def push_effect(effect: EffectLike) -> None:
    _active_effects.append(effect)


def pop_effect() -> None:
    _active_effects.pop()


def get_active_effect() -> EffectLike | None:
    if not _active_effects:
        return None

    return _active_effects[-1]


def schedule_effect(effect: EffectLike) -> None:
    if effect in _active_effects:
        return

    if _batch_depth > 0 or _is_flushing:
        _pending_effects[effect] = None
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
            del _pending_effects[effect]
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


def _pause_tracking() -> list[EffectLike]:
    active_effects = _active_effects.copy()
    _active_effects.clear()
    return active_effects


def _restore_tracking(active_effects: list[EffectLike]) -> None:
    _active_effects[:] = active_effects


def peek[T](value: Peekable[T]) -> T:
    """Read a reactive value without tracking it as a dependency."""

    return value._peek()


def dispose(value: Disposable) -> None:
    """Stop a reactive value from receiving future updates."""

    value._dispose()
