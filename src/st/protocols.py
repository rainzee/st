from collections.abc import Callable
from typing import Protocol


class Source(Protocol):
    """Reactive value that can be tracked by computations."""

    def _subscribe(self, computation: "Computation") -> None: ...

    def _unsubscribe(self, computation: "Computation") -> None: ...


class Computation(Protocol):
    """Reactive computation that tracks sources and can be scheduled."""

    _priority: int

    def __call__(self) -> None: ...

    def _depend_on(self, source: Source) -> None: ...


class CleanupTarget(Computation, Protocol):
    """Computation that can collect cleanup callbacks for its current run."""

    def _add_cleanup(self, cleanup: "Cleanup") -> None: ...


class Peekable[T](Protocol):
    """Reactive value that supports non-tracking reads."""

    def _peek(self) -> T: ...


class Disposable(Protocol):
    """Reactive resource that can be stopped or released."""

    def _dispose(self) -> None: ...


type Cleanup = Callable[[], None]
