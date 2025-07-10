# Developer Examples

This project no longer bundles the old `user_plugins/examples` directory. The docs now include a minimal example so you can experiment quickly.

## Minimal Pipeline

Create a simple agent that echoes input back through the HTTP adapter:

```python
from entity.core.agent import Agent
from plugins.builtin.adapters.http import HTTPAdapter
from plugins.builtin.prompts.echo import EchoPrompt

agent = Agent()
agent.add_plugin(EchoPrompt())
agent.add_plugin(HTTPAdapter(stages=["parse", "deliver"]))

if __name__ == "__main__":
    agent.run()
```

Run the agent with:

```bash
poetry run python src/main.py
```

For additional pipeline recipes, see the example projects linked in the README.

