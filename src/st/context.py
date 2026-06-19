from collections.abc import Callable
from typing import overload

from st.protocols import Computation
from st.runtime import _begin_batch, _end_batch, _pause_tracking, _restore_tracking


class UntrackContext:
    def __init__(self) -> None:
        self._active_computations: list[Computation] = []

    def __enter__(self) -> None:
        self._active_computations = _pause_tracking()

    def __exit__(self, *args: object) -> None:
        _restore_tracking(self._active_computations)


class BatchContext:
    def __enter__(self) -> None:
        _begin_batch()

    def __exit__(self, *args: object) -> None:
        _end_batch()


@overload
def untrack() -> UntrackContext: ...


@overload
def untrack[T](function: Callable[[], T]) -> T: ...


def untrack[T](function: Callable[[], T] | None = None) -> T | UntrackContext:
    """Disable dependency tracking for a function or context block."""

    context = UntrackContext()
    if function is None:
        return context

    with context:
        return function()


@overload
def batch() -> BatchContext: ...


@overload
def batch[T](function: Callable[[], T]) -> T: ...


def batch[T](function: Callable[[], T] | None = None) -> T | BatchContext:
    """Defer reactive updates for a function or context block."""

    context = BatchContext()
    if function is None:
        return context

    with context:
        return function()
