# st

Minimal reactive state for Python.

## Design

`st` is built around a small idea: reactive state should feel ordinary in Python.
Values are plain objects with a `.value`, derived state is lazy, and side effects
are owned explicitly instead of hidden behind framework magic.

The runtime favors a clear reactive graph over a large abstraction surface.
Sources notify computations, computations track their sources, and scopes make
ownership visible. Updates are synchronous and deterministic by default, so the
mental model stays close to the code you write.

- Small core. No runtime dependencies.
- Signal-first model. State, derived state, and effects form the primitive graph.
- Structural typing. Internal contracts use `Protocol`, not inheritance.
- Python 3.13 generics. `State[T]` and `Computed[T]` use PEP 695 syntax.
- Dynamic dependencies. Effects replace their dependency set on each run.
- Equality short-circuit. Unchanged values do not notify dependents.

## API

| API | Purpose |
| --- | --- |
| `state(value, *, equals=...)` | Create mutable reactive state. |
| `computed(fn)` | Create lazy derived state. |
| `effect(fn)` | Run a side effect with automatic dependency tracking. |
| `watch(source, callback, *, immediate=False)` | Watch an explicit source with `new`, `old`, and optional cleanup. |
| `readonly(value)` | Expose a read-only view of state or computed state. |
| `batch()` | Coalesce updates and flush effects once. |
| `untrack()` | Read reactive values without collecting dependencies. |
| `peek(value)` | Read a reactive value without tracking. |
| `scope()` | Own effects, computed values, watchers, and cleanup callbacks. |
| `on_cleanup(fn)` | Register cleanup on the current effect or scope. |
| `dispose(value)` | Stop a disposable reactive resource. |

## Examples

- [Shopping cart](examples/shopping_cart.py): cart totals, coupons, checkout validation, scoped cleanup, and batched updates.

```shell
uv run python examples/shopping_cart.py
```

## Usage

### State

```python
from st import state

count = state(1)

count.value = 2

assert count.value == 2
```

### Computed values

```python
from st import computed, state

count = state(1)
double = computed(lambda: count.value * 2)

assert double.value == 2

count.value = 2

assert double.value == 4
```

### Read-only views

```python
from st import readonly, state

count = state(1)
public_count = readonly(count)

count.value = 2

assert public_count.value == 2
```

### Custom equality

```python
from st import effect, state

count = state(1, equals=lambda old, new: old % 2 == new % 2)
values: list[int] = []

effect(lambda: values.append(count.value))

count.value = 3
count.value = 4

assert values == [1, 4]
```

### Effects

```python
from st import effect, state

count = state(1)
values: list[int] = []

effect(lambda: values.append(count.value))

count.value = 2

assert values == [1, 2]
```

### Watching explicit sources

```python
from st import watch, state

count = state(1)
values: list[tuple[int, int | None]] = []

watch(lambda: count.value, lambda new, old: values.append((new, old)))

count.value = 2

assert values == [(2, 1)]
```

```python
from st import watch, state

count = state(1)
values: list[str] = []

def sync(new: int, old: int | None, on_cleanup) -> None:
    on_cleanup(lambda: values.append(f"cleanup {new}"))
    values.append(f"{old}->{new}")

watch(lambda: count.value, sync, immediate=True)
count.value = 2

assert values == ["None->1", "cleanup 1", "1->2"]
```

### Effect cleanup

```python
from st import effect, on_cleanup, state

count = state(1)
values: list[str] = []

def sync() -> None:
    value = count.value
    on_cleanup(lambda: values.append(f"cleanup {value}"))
    values.append(f"run {value}")

effect(sync)
count.value = 2

assert values == ["run 1", "cleanup 1", "run 2"]
```

### Untracked reads

```python
from st import effect, peek, state, untrack

count = state(1)
values: list[int] = []

def collect() -> None:
    with untrack():
        value = count.value
    values.append(value)

effect(collect)

count.value = 2

assert values == [1]
assert peek(count) == 2
```

### Batched updates

```python
from st import batch, effect, state

count = state(1)
values: list[int] = []

effect(lambda: values.append(count.value))

with batch():
    count.value = 2
    count.value = 3

assert values == [1, 3]
```

### Disposal

```python
from st import dispose, effect, state

count = state(1)
values: list[int] = []

effect_ = effect(lambda: values.append(count.value))
effect_.dispose()

count.value = 2

assert values == [1]
```

### Scopes

```python
from st import effect, on_cleanup, scope, state

count = state(1)
values: list[int] = []
owner = scope()

def setup() -> None:
    effect(lambda: values.append(count.value))
    on_cleanup(lambda: values.append(-1))

owner.run(setup)
count.value = 2
owner.dispose()

assert values == [1, 2, -1]
```

## Roadmap

Core infrastructure:

- `dispose` (done)
- `untrack` (done)
- `peek` (done)
- `batch` (done)
- `on_cleanup` (done)

Scheduling:

- custom effect schedulers
- queued flush
- `next_tick`

Debugging:

- runtime type guards
- dependency inspection
- subscriber inspection
- optional labels

## Development

```shell
uv sync
uv run pytest
```
