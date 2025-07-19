# Example Agents

Each subdirectory demonstrates a specific capability.

- **basic_agent** – simplest echo example.
- **default** – decorator-based workflow with one tool.
- **default_setup** – global agent initialized automatically.
- **duckdb_memory_agent** – custom memory backed by DuckDB.
- **full_workflow** – multiple LLM providers with PostgreSQL, a vector store,
  and metrics.
- **intermediate_agent** – chained prompt and responder plugins.
- **kitchen_sink** – small ReAct loop using the calculator tool.

Run any example with:

```bash
poetry run python examples/<name>/main.py
```

The `PluginContext` in each example provides `get_llm()`, `get_memory()`,
`get_storage()`, and `get_resource("logging")` for unified logging access.
