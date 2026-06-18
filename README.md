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

```python
from st import State, computed, effect, peek

count = State(1)
double = computed(lambda: count.value * 2)

effect(lambda: print(double.value))

count.value = 2

current = peek(double)
```

Output:

```text
2
4
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
