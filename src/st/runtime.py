from typing import TypeIs

from st.protocols import Cleanup, CleanupTarget, Computation, Disposable, Peekable, Source

_active_computations: list[Computation] = []
_batch_depth = 0
_pending_computations: dict[Computation, None] = {}
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


def track_source(source: Source) -> None:
    if _active_computations:
        _active_computations[-1]._depend_on(source)


def push_computation(computation: Computation) -> None:
    _active_computations.append(computation)


def pop_computation() -> None:
    _active_computations.pop()


def get_active_computation() -> Computation | None:
    if not _active_computations:
        return None

    return _active_computations[-1]


def collects_cleanup(computation: Computation) -> TypeIs[CleanupTarget]:
    return hasattr(computation, "_add_cleanup")


def schedule_computation(computation: Computation) -> None:
    if computation in _active_computations:
        return

    if _batch_depth > 0 or _is_flushing:
        _pending_computations[computation] = None
        return

    computation()


def _flush_computations() -> None:
    global _is_flushing

    if _is_flushing:
        return

    _is_flushing = True
    try:
        while _pending_computations:
            computation = min(_pending_computations, key=lambda item: item._priority)
            del _pending_computations[computation]
            computation()
    finally:
        _is_flushing = False


def _begin_batch() -> None:
    global _batch_depth

    _batch_depth += 1


def _end_batch() -> None:
    global _batch_depth

    _batch_depth -= 1
    if _batch_depth == 0:
        _flush_computations()


def _pause_tracking() -> list[Computation]:
    active_computations = _active_computations.copy()
    _active_computations.clear()
    return active_computations


def _restore_tracking(active_computations: list[Computation]) -> None:
    _active_computations[:] = active_computations


def peek[T](value: Peekable[T]) -> T:
    """Read a reactive value without tracking it as a source."""

    return value._peek()


def dispose(value: Disposable) -> None:
    """Stop a reactive value from receiving future updates."""

    value._dispose()
