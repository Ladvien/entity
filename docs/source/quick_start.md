# Quick Start

Follow these steps to get a basic agent running.

## 1. Install

Ready-made agents live in the new `examples/` directory. Run them with
`poetry run python examples/<name>/main.py` to see the framework in action.

### Programmatic Configuration
Build the same configuration in Python using the models from
`entity.config`. The `Memory` resource sets up an in-memory DuckDB database by default so no database server is required:

```python
from entity.config.models import EntityConfig, PluginsSection, PluginConfig

config = EntityConfig(
    workflow={"think": ["main"], "deliver": ["http"]},
    plugins=PluginsSection(
        prompts={"main": PluginConfig(type="user_plugins.prompts.simple:SimplePrompt")},
        adapters={"http": PluginConfig(type="plugins.builtin.adapters.http:HTTPAdapter", stages=["parse", "deliver"])},
        resources={
            "llm": PluginConfig(provider="openai", model="gpt-4"),
            "memory": PluginConfig(type="entity.resources.memory:Memory"),
        },
    ),
)
```

```bash
pip install entity
# or
poetry add entity
```

## 2. Scaffold a project

Create a starter layout using the built-in generator:

```bash
entity-cli new my_agent
cd my_agent
```

This command creates `config/dev.yaml` and `src/main.py`.

## 3. Run the sample agent

Start the HTTP server and send a message:

```bash
poetry run python src/main.py
curl -X POST -H "Content-Type: application/json" \
     -d '{"message": "hello"}' http://localhost:8000/
```

You should see a simple reply from the example pipeline.

The generated configuration stores conversation history in an in-memory DuckDB database. You can switch to a file-based or server database later by editing `config/dev.yaml`.

## Troubleshooting

- Activate your virtual environment if `entity-cli` is not found.
- Missing packages? Run `poetry install --with dev` in the project root.
- Use `--debug` with any command for verbose logs.

## What's next?

Head over to the [Plugin Development Guide](plugin_guide.md) to extend the agent with custom logic.
