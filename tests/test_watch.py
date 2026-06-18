import pytest

from st import State, dispose, scope, watch


def test_watch_calls_callback_with_new_and_old_values() -> None:
    count = State(1)
    values: list[tuple[int, int | None]] = []

    watch(lambda: count.value, lambda new, old: values.append((new, old)))

    count.value = 2
    count.value = 3

    assert values == [(2, 1), (3, 2)]


def test_watch_can_run_immediately() -> None:
    count = State(1)
    values: list[tuple[int, int | None]] = []

    watch(lambda: count.value, lambda new, old: values.append((new, old)), immediate=True)

    assert values == [(1, None)]


def test_watch_skips_equal_source_values() -> None:
    count = State(1)
    values: list[tuple[int, int | None]] = []

    watch(lambda: count.value % 2, lambda new, old: values.append((new, old)))

    count.value = 3
    count.value = 4

    assert values == [(0, 1)]


def test_watch_only_tracks_the_source() -> None:
    source = State(1)
    other = State("a")
    values: list[tuple[int, str]] = []

    watch(lambda: source.value, lambda new, _old: values.append((new, other.value)))

    other.value = "b"
    source.value = 2

    assert values == [(2, "b")]


def test_watch_runs_cleanup_before_next_callback() -> None:
    count = State(1)
    values: list[str] = []

    def callback(new: int, _old: int | None, on_cleanup) -> None:
        on_cleanup(lambda: values.append(f"cleanup {new}"))
        values.append(f"run {new}")

    watch(lambda: count.value, callback, immediate=True)
    count.value = 2

    assert values == ["run 1", "cleanup 1", "run 2"]


def test_watch_runs_cleanup_when_disposed() -> None:
    count = State(1)
    values: list[str] = []

    watcher = watch(
        lambda: count.value,
        lambda new, _old, on_cleanup: on_cleanup(lambda: values.append(f"cleanup {new}")),
        immediate=True,
    )

    watcher.dispose()
    count.value = 2

    assert values == ["cleanup 1"]


def test_dispose_stops_watch() -> None:
    count = State(1)
    values: list[int] = []

    watcher = watch(lambda: count.value, lambda new, _old: values.append(new))
    dispose(watcher)
    count.value = 2

    assert values == []


def test_scope_disposes_watchers_on_exit() -> None:
    count = State(1)
    values: list[int] = []

    with scope():
        watch(lambda: count.value, lambda new, _old: values.append(new))

    count.value = 2

    assert values == []


def test_watch_disposes_initial_dependencies_when_initial_source_raises() -> None:
    count = State(1)
    calls: list[int] = []

    def source() -> int:
        calls.append(count.value)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        watch(source, lambda _new, _old: None)

    count.value = 2

    assert calls == [1]
