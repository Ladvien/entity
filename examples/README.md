# Example Agents

Each subdirectory contains a small agent showcasing different features.

- **kitchen_sink** – demonstrates a ReAct loop with tool usage.
- **default** – minimal zero-config agent using decorators.
- **plugins** – minimal plugins for INPUT, PARSE, and REVIEW stages.
- **full_workflow** – multiple LLM providers with PostgreSQL and monitoring.

Run any example with:

```bash
poetry run python examples/<name>/main.py
```

The `PluginContext` in each example provides `get_llm()`, `get_memory()`,
`get_storage()`, and `get_resource("logging")` for unified logging access.
