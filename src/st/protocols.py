from collections.abc import Callable
from typing import Protocol


class Dependency(Protocol):
    """Reactive value that can be observed by observers."""

    def _subscribe(self, observer: "Observer") -> None: ...

    def _unsubscribe(self, observer: "Observer") -> None: ...


class Observer(Protocol):
    """Reactive computation that tracks dependencies and can be scheduled."""

    def __call__(self) -> None: ...

    def _depend_on(self, dependency: Dependency) -> None: ...


class CleanupOwner(Observer, Protocol):
    """Observer that can own cleanup callbacks for its current run."""

    def _add_cleanup(self, cleanup: "Cleanup") -> None: ...


class Peekable[T](Protocol):
    """Reactive value that supports non-tracking reads."""

    def _peek(self) -> T: ...


class Disposable(Protocol):
    """Reactive resource that can be stopped or released."""

    def _dispose(self) -> None: ...


type Cleanup = Callable[[], None]
