# st

Minimal reactive state for Python.

## Design

- Small core. No runtime dependencies.
- Signal-first model. State, derived state, and effects form the primitive graph.
- Structural typing. Internal contracts use `Protocol`, not inheritance.
- Python 3.13 generics. `State[T]` and `Computed[T]` use PEP 695 syntax.
- Dynamic dependencies. Effects replace their dependency set on each run.
- Equality short-circuit. Unchanged values do not notify dependents.

## Usage

### State

```python
from st import State

count = State(1)

count.value = 2

assert count.value == 2
```

### Computed values

```python
from st import State, computed

count = State(1)
double = computed(lambda: count.value * 2)

assert double.value == 2

count.value = 2

assert double.value == 4
```

### Effects

```python
from st import State, effect

count = State(1)
values: list[int] = []

effect(lambda: values.append(count.value))

count.value = 2

assert values == [1, 2]
```

### Untracked reads

```python
from st import State, effect, peek, untrack

count = State(1)
values: list[int] = []

effect(lambda: values.append(untrack(lambda: count.value)))

count.value = 2

assert values == [1]
assert peek(count) == 2
```

### Batched updates

```python
from st import State, batch, effect

count = State(1)
values: list[int] = []

effect(lambda: values.append(count.value))

def update() -> None:
    count.value = 2
    count.value = 3

batch(update)

assert values == [1, 3]
```

### Disposal

```python
from st import State, dispose, effect

count = State(1)
values: list[int] = []

effect_ = effect(lambda: values.append(count.value))
dispose(effect_)

count.value = 2

assert values == [1]
```

## Roadmap

Core infrastructure:

- `dispose` (done)
- `untrack` (done)
- `peek` (done)
- `batch` (done)
- `on_cleanup`

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
