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


_active_effects: list[EffectLike] = []
_batch_depth = 0
_pending_effects: set[EffectLike] = set()
_is_flushing = False


def track_dependency(dependency: Dependency) -> None:
    if _active_effects:
        _active_effects[-1]._depend_on(dependency)


def push_effect(effect: EffectLike) -> None:
    _active_effects.append(effect)


def pop_effect() -> None:
    _active_effects.pop()


def schedule_effect(effect: EffectLike) -> None:
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


def peek[T](value: Peekable[T]) -> T:
    """Read a reactive value without tracking it as a dependency."""

    return value._peek()


def untrack[T](function: Callable[[], T]) -> T:
    """Run a function without tracking reactive reads as dependencies."""

    active_effects = _active_effects.copy()
    _active_effects.clear()
    try:
        return function()
    finally:
        _active_effects[:] = active_effects


def batch[T](function: Callable[[], T]) -> T:
    """Run a function and defer reactive updates until it completes."""

    global _batch_depth

    _batch_depth += 1
    try:
        return function()
    finally:
        _batch_depth -= 1
        if _batch_depth == 0:
            _flush_effects()


def dispose(value: Disposable) -> None:
    """Stop a reactive value from receiving future updates."""

    value._dispose()
