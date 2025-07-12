# Example Agents

Each subdirectory contains a small agent showcasing a different feature level.

- **basic_agent** – echoes the user's message.
- **intermediate_agent** – runs a chain-of-thought prompt with an echo LLM.
- **advanced_agent** – demonstrates a ReAct loop with tool usage.
- **zero_config_agent** – uses `@agent.tool` and `@agent.prompt` decorators.

Run any example with:

```bash
poetry run python examples/<name>/main.py
```

The `PluginContext` in each example provides `get_llm()`, `get_memory()`,
`get_storage()`, and `get_resource("logging")` for unified logging access.
