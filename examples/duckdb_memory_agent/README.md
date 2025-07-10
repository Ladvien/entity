# DuckDB Memory Agent

This example runs a minimal pipeline with a DuckDB-backed memory resource.
It increments a counter on each request and persists it to `agent.duckdb`.

```bash
poetry run python examples/duckdb_memory_agent/main.py
```

Run the script twice and inspect the database file:

```bash
duckdb agent.duckdb "SELECT * FROM kv;"
```
