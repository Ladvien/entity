# Entity Examples

Learn by example. Each directory contains a complete, working agent.

## Quick Start

```bash
pip install entity-core
cd hello_agent && python hello_agent.py
```

## Examples by Complexity

### 🟢 Beginner
- **hello_agent** - Zero config agent (3 lines)
- **agent_personality** - YAML-driven personalities
- **conversation_memory** - Persistent state

### 🟡 Intermediate
- **tool_usage** - Custom plugins and tools
- **simple_chat** - Complete chat system
- **streaming_responses** - Real-time output

### 🔴 Advanced
- **code_reviewer** - Production code analysis
- **research_assistant** - Multi-source research
- **framework_showcase** - All features demo

## Core Pattern

```python
# Every agent follows: Agent = Resources + Workflow
from entity import Agent

agent = Agent()  # Defaults
await agent.chat("Hello!")
```

## Custom Plugin

```python
from entity.plugins.base import Plugin

class MyTool(Plugin):
    supported_stages = ["do"]

    async def _execute_impl(self, context):
        return f"Processed: {context.message}"

# Use it
agent = Agent(plugins={"do": [MyTool()]})
```

## YAML Configuration

```yaml
# config.yaml
plugins:
  think: [reasoning_plugin]
  do: [calculator, web_search]
```

```python
agent = Agent.from_config("config.yaml")
```

## Run Any Example

```bash
python examples/<name>/<name>.py
```

## Docs

[entity-core.readthedocs.io](https://entity-core.readthedocs.io/)
