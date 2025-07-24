# Entity Framework
Python agent framework

## Examples
Run `python -m entity.examples` to see sample workflows. The old `[examples]` extra has been removed.

## Persistent Memory

Entity uses a DuckDB database to store all remembered values. Keys are
namespaced by user ID to keep data isolated between users. The `Memory` API is
asynchronous and protected by an internal lock so concurrent workflows remain
thread safe.

## Plugin Lifecycle

Plugins are validated before any workflow executes:

1. **Configuration validation** – each plugin defines a `ConfigModel` and the
   `validate_config` classmethod parses user options with Pydantic.
2. **Workflow validation** – `validate_workflow` is called when workflows are
   built to ensure a plugin supports its assigned stage.
3. **Execution** – once instantiated with resources, validated plugins run
   without further checks.

Entity stores all remembered values inside a DuckDB database. Keys are
automatically prefixed with the user ID so data never leaks across users. The
`Memory` API exposes asynchronous helpers that run queries in a background
thread while holding an internal `asyncio.Lock`.

```python
infra = DuckDBInfrastructure("agent.db")
memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
await memory.store("bob:greeting", "hello")
```
