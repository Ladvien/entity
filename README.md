# Entity Framework
Python agent framework

## Examples
Run `python -m entity.examples` to see sample workflows. The old `[examples]` extra has been removed.

## Persistent Memory

Entity uses a DuckDB database to store all remembered values. Each key is automatically namespaced by the user ID to keep data isolated between users. The memory API is fully asynchronous and guarded by an internal lock so concurrent workflows remain thread safe.
