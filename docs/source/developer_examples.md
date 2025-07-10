# Developer Examples

This repository ships a few self-contained example agents under ``examples/``.

| Example | Description |
| ------- | ----------- |
| ``basic_agent`` | Minimal echo agent |
| ``intermediate_agent`` | Chain-of-thought reasoning with an echo LLM |
| ``advanced_agent`` | ReAct loop using the calculator tool |

Run any example with ``poetry run python examples/<name>/main.py``.

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

