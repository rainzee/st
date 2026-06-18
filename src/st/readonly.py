from typing import Protocol


class Readable[T](Protocol):
    @property
    def value(self) -> T: ...

    def _peek(self) -> T: ...


class Readonly[T]:
    """Read-only view of a reactive value."""

    def __init__(self, value: Readable[T]) -> None:
        self._value = value

    @property
    def value(self) -> T:
        """Current value."""

        return self._value.value

    def _peek(self) -> T:
        return self._value._peek()


def readonly[T](value: Readable[T]) -> Readonly[T]:
    """Create a read-only view of a reactive value."""

    return Readonly(value)
