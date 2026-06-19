from typing import TypeIs

from st.protocols import Cleanup, CleanupOwner, Dependency, Disposable, Observer, Peekable

_active_observers: list[Observer] = []
_batch_depth = 0
_pending_observers: dict[Observer, None] = {}
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
    if _active_observers:
        _active_observers[-1]._depend_on(dependency)


def push_observer(observer: Observer) -> None:
    _active_observers.append(observer)


def pop_observer() -> None:
    _active_observers.pop()


def get_active_observer() -> Observer | None:
    if not _active_observers:
        return None

    return _active_observers[-1]


def owns_cleanup(observer: Observer) -> TypeIs[CleanupOwner]:
    return hasattr(observer, "_add_cleanup")


def schedule_observer(observer: Observer) -> None:
    if observer in _active_observers:
        return

    if _batch_depth > 0 or _is_flushing:
        _pending_observers[observer] = None
        return

    observer()


def _flush_observers() -> None:
    global _is_flushing

    if _is_flushing:
        return

    _is_flushing = True
    try:
        while _pending_observers:
            observer = min(_pending_observers, key=lambda item: getattr(item, "_priority", 1))
            del _pending_observers[observer]
            observer()
    finally:
        _is_flushing = False


def _begin_batch() -> None:
    global _batch_depth

    _batch_depth += 1


def _end_batch() -> None:
    global _batch_depth

    _batch_depth -= 1
    if _batch_depth == 0:
        _flush_observers()


def _pause_tracking() -> list[Observer]:
    active_observers = _active_observers.copy()
    _active_observers.clear()
    return active_observers


def _restore_tracking(active_observers: list[Observer]) -> None:
    _active_observers[:] = active_observers


def peek[T](value: Peekable[T]) -> T:
    """Read a reactive value without tracking it as a dependency."""

    return value._peek()


def dispose(value: Disposable) -> None:
    """Stop a reactive value from receiving future updates."""

    value._dispose()
