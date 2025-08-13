# Entity Framework 🚀

[![PyPI](https://badge.fury.io/py/entity-core.svg)](https://badge.fury.io/py/entity-core)
[![Docs](https://readthedocs.org/projects/entity-core/badge/?version=latest)](https://entity-core.readthedocs.io)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/Ladvien/entity/workflows/tests/badge.svg)](https://github.com/Ladvien/entity/actions)

**Build AI agents in minutes, not weeks.**

## Quick Start

```bash
pip install entity-core
```

```python
from entity import Agent

agent = Agent()  # Zero config
response = await agent.chat("Hello!")  # Ready to use
```

## Core Concept

```python
# Agent = Resources + Workflow
from entity import Agent
from entity.defaults import load_defaults

agent = Agent(
    resources=load_defaults(),  # Memory, LLM, Storage
    workflow=default_workflow()  # 6-stage pipeline
)
```

## Progressive Examples

### 1. Basic Agent (3 lines)
```python
from entity import Agent
agent = Agent()
await agent.chat("Tell me a joke")
```

### 2. Custom Personality (5 lines)
```python
agent = Agent.from_config({
    "role": "You are a Python tutor",
    "plugins": {"think": ["reasoning_plugin"]}
})
await agent.chat("Explain decorators")
```

### 3. Agent with Tools (8 lines)
```python
from entity.tools import calculator, web_search

agent = Agent.from_config({
    "plugins": {
        "do": [calculator, web_search]
    }
})
await agent.chat("Search Python 3.12 features and calculate 15% of 200")
```

### 4. Production Setup (10 lines)
```python
from entity import Agent
from entity.monitoring import setup_observability

agent = Agent.from_config("production.yaml")
setup_observability(agent)
await agent.serve(port=8000)
```

## Architecture: 6-Stage Pipeline

```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```

Each stage accepts plugins:

```python
workflow = {
    "input": [TextAdapter()],      # Accept input
    "parse": [IntentParser()],     # Understand
    "think": [ReasoningEngine()],  # Plan
    "do": [ToolExecutor()],        # Execute
    "review": [SafetyFilter()],    # Validate
    "output": [Formatter()]         # Deliver
}
```

## Plugin Development

```python
from entity.plugins.base import Plugin

class MyPlugin(Plugin):
    supported_stages = ["think"]

    async def _execute_impl(self, context):
        # Your logic here
        return f"Processed: {context.message}"

# Use it
agent = Agent(plugins={"think": [MyPlugin()]})
```

## Installation Options

```bash
# Basic
pip install entity-core

# With extras
pip install "entity-core[web,dev]"

# From source
git clone --recurse-submodules https://github.com/Ladvien/entity.git
cd entity && pip install -e .
```

## Plugin Packages

```bash
# Optional plugins
pip install entity-plugin-gpt-oss  # Advanced reasoning
pip install entity-plugin-stdlib   # Standard tools
```

## Real-World Configurations

### Customer Support
```yaml
# support.yaml
plugins:
  parse: [intent_classifier, sentiment_analyzer]
  do: [knowledge_base, ticket_system]
  review: [compliance_checker]
```

### Code Reviewer
```yaml
# reviewer.yaml
plugins:
  parse: [diff_parser, ast_analyzer]
  think: [pattern_matcher]
  do: [security_scanner, style_checker]
  output: [github_commenter]
```

## Why Entity?

| Metric | Traditional | Entity |
|--------|------------|--------|
| Dev Time | 2-3 weeks | 2-3 days |
| Code Lines | 2000+ | ~200 |
| Architecture | Monolithic | Plugin-based |
| Testing | Complex | Simple units |

## Resources

- [Documentation](https://entity-core.readthedocs.io/)
- [Examples](examples/)
- [Plugin Registry](https://plugins.entity.dev)
- [GitHub](https://github.com/Ladvien/entity)

## License

MIT

---

**Build better agents, faster.** 🚀
