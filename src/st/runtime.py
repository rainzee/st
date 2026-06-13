from typing import Protocol


class Dependency(Protocol):
    def _subscribe(self, effect: "EffectLike") -> None: ...

    def _unsubscribe(self, effect: "EffectLike") -> None: ...


class EffectLike(Protocol):
    def __call__(self) -> None: ...

    def _depend_on(self, dependency: Dependency) -> None: ...


_active_effects: list[EffectLike] = []


def track_dependency(dependency: Dependency) -> None:
    if _active_effects:
        _active_effects[-1]._depend_on(dependency)


def push_effect(effect: EffectLike) -> None:
    _active_effects.append(effect)


def pop_effect() -> None:
    _active_effects.pop()
