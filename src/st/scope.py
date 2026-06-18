from collections.abc import Callable

from st.runtime import Cleanup, Disposable


_active_scopes: list["Scope"] = []


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

    def run[T](self, setup: Callable[[], T]) -> T:
        """Run setup in this scope without disposing when setup completes."""

        if self._disposed:
            raise RuntimeError("Cannot run a disposed scope")

        _active_scopes.append(self)
        try:
            return setup()
        except BaseException:
            self._dispose()
            raise
        finally:
            _active_scopes.pop()

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


def scope() -> Scope:
    """Create an owner scope for reactive resources."""

    return Scope()


def register_cleanup(cleanup: Cleanup) -> None:
    if not _active_scopes:
        raise RuntimeError("on_cleanup() requires an active scope")

    _active_scopes[-1]._add_cleanup(cleanup)


def register_disposable(disposable: Disposable) -> None:
    if _active_scopes:
        _active_scopes[-1]._add_cleanup(disposable._dispose)


def on_cleanup(cleanup: Cleanup) -> None:
    """Register a cleanup callback on the current scope."""

    register_cleanup(cleanup)
