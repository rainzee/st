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


def track_dependency(dependency: Dependency) -> None:
    if _active_effects:
        _active_effects[-1]._depend_on(dependency)


def push_effect(effect: EffectLike) -> None:
    _active_effects.append(effect)


def pop_effect() -> None:
    _active_effects.pop()


def peek[T](value: Peekable[T]) -> T:
    """Read a reactive value without tracking it as a dependency."""

    return value._peek()


def dispose(value: Disposable) -> None:
    """Stop a reactive value from receiving future updates."""

    value._dispose()
