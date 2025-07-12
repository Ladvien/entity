# Example Agents

Each subdirectory contains a small agent showcasing a different feature level.

- **kitchen_sink** – demonstrates a ReAct loop with tool usage.
- **default_setup** – uses `@agent.tool` and `@agent.prompt` decorators.

Run any example with:

```bash
poetry run python examples/<name>/main.py
```

The `PluginContext` in each example provides `get_llm()`, `get_memory()`,
`get_storage()`, and `get_resource("logging")` for unified logging access.
