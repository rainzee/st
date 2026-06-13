# st

Minimal reactive state for Python.

`State` stores a value. `effect` tracks every state read during execution and
reruns when those dependencies change. `computed` derives read-only state from
other state.

## Usage

```python
from st import State, computed, effect

count = State(1)
double = computed(lambda: count.value * 2)

effect(lambda: print(double.value))

count.value = 2
```

Output:

```text
2
4
```

## Roadmap

Core infrastructure:

- `dispose`
- `untrack`
- `peek`
- `batch`
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
