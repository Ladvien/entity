# DuckDB Memory Agent

This example defines a custom `DuckDBMemory` resource that persists key-value pairs and conversation history in a local DuckDB file. Each run increments a counter stored in the database.

```bash
poetry run python examples/duckdb_memory_agent/main.py
```
