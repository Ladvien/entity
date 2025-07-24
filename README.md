# Entity Framework
Python agent framework

## Examples
Run `python -m entity.examples` to see sample workflows. The old `[examples]` extra has been removed.

## Persistent Memory

<<<<<<< HEAD
Entity uses a DuckDB database to store all remembered values. Each key is automatically namespaced by the user ID to keep data isolated between users. The memory API is fully asynchronous and guarded by an internal lock so concurrent workflows remain thread safe.

## Plugin Lifecycle

Plugins are validated before any workflow executes:

1. **Configuration validation** &mdash; each plugin defines a `ConfigModel` and
   the classmethod `validate_config` uses Pydantic to parse user supplied
   options.
2. **Workflow validation** &mdash; `validate_workflow` ensures the plugin is
   placed in a supported stage during workflow construction.
3. **Execution** &mdash; once instantiated with resources, plugins run without
   additional checks.
=======
Entity stores all remembered values inside a DuckDB database. Keys are automatically prefixed with the user ID so data never leaks across users. The `Memory` API exposes asynchronous `store` and `load` helpers which run queries in a background thread while holding an internal `asyncio.Lock`. This design keeps concurrent workflows safe even when multiple users interact with the same agent.

```python
infra = DuckDBInfrastructure("agent.db")
memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
await memory.store("bob:greeting", "hello")
```
>>>>>>> pr-1889
