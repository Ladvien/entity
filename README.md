# Entity Framework
Python agent framework

## Examples
Run `python -m entity.examples` to see sample workflows. The old `[examples]` extra has been removed.

## Persistent Memory

Entity stores all remembered values inside a DuckDB database. Keys are automatically prefixed with the user ID so data never leaks across users. The `Memory` API exposes asynchronous `store` and `load` helpers which run queries in a background thread while holding an internal `asyncio.Lock`. This design keeps concurrent workflows safe even when multiple users interact with the same agent.

```python
infra = DuckDBInfrastructure("agent.db")
memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
await memory.store("bob:greeting", "hello")
```
