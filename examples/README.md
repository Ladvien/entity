# Example Agents

Each subdirectory contains a small agent showcasing a different feature level.

- **basic_agent** – echoes the user's message.
- **intermediate_agent** – runs a chain-of-thought prompt with an echo LLM.
- **advanced_agent** – demonstrates a ReAct loop with tool usage.

Run any example with:

```bash
poetry run python examples/<name>/main.py
```

The `PluginContext` in each example provides `get_llm()`, `get_memory()`, and `get_storage()` helpers for quick resource access.
