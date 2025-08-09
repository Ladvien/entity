# Entity Framework Examples

Build production-ready AI agents 10x faster with Entity's plugin architecture.

## The 6-Stage Pipeline

Every Entity agent processes data through six stages:

**INPUT → PARSE → THINK → DO → REVIEW → OUTPUT**

Each stage can have multiple plugins that execute in sequence, making complex behaviors simple to compose.

## Getting Started Examples

### hello_agent - Zero Configuration
The simplest possible Entity agent in just a few lines:
```python
from entity import Agent
from entity.defaults import load_defaults

agent = Agent(resources=load_defaults())
await agent.chat("")
```

### agent_personality - Configuration-Driven
Define agent behavior through YAML:
```bash
python personality_agent.py python_tutor.yaml
python personality_agent.py creative_writer.yaml
python personality_agent.py business_consultant.yaml
```

### tool_usage - Custom Plugins
Build your own tools and integrate them into the pipeline:
```python
class WordAnalyzer(ToolPlugin):
    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context):
        words = len(context.message.split())
        return f"Word count: {words}"
```

### conversation_memory - Persistent State
Agents that remember across sessions:
```python
# In any plugin
await context.remember("user_name", "Alice")
name = await context.recall("user_name")  # Returns "Alice" next session
```

## Advanced Examples

### simple_chat
Complete chat agent showing plugin inheritance patterns and YAML configuration.

### code_reviewer
Production-ready code analysis with security scanning and style checking.

### research_assistant
Multi-source research with web search, paper fetching, and synthesis.

### framework_showcase
Comprehensive demo of all Entity features in one agent.

## Quick Start

1. Install Entity:
```bash
pip install entity-core
```

2. Run any example:
```bash
cd hello_agent
python hello_agent.py
```

## Creating Your Own Agent

### Basic Pattern
```python
# 1. Load resources
resources = load_defaults()

# 2. Define workflow
workflow = {
    "input": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
    "think": ["entity.plugins.prompt.PromptPlugin"],
    "do": ["YourCustomPlugin"],
    "output": ["entity.cli.ent_cli_adapter.EntCLIAdapter"]
}

# 3. Create and run
agent = Agent.from_workflow_dict(workflow, resources=resources)
await agent.chat("")
```

### With Configuration
```yaml
# agent_config.yaml
resources:
  llm:
    temperature: 0.7
    system_prompt: "You are a helpful assistant"

workflow:
  input: ["entity.cli.ent_cli_adapter.EntCLIAdapter"]
  think: ["entity.plugins.prompt.PromptPlugin"]
  do: ["your_module.YourPlugin"]
  output: ["entity.cli.ent_cli_adapter.EntCLIAdapter"]
```

```python
agent = Agent.from_config("agent_config.yaml")
await agent.chat("")
```

## Plugin Development

### Basic Plugin Structure
```python
from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor

class MyPlugin(Plugin):
    supported_stages = [WorkflowExecutor.THINK]  # or DO, REVIEW, etc.
    dependencies = ["memory", "llm"]  # Required resources

    async def _execute_impl(self, context):
        # Your logic here
        result = process(context.message)
        return result
```

### Available Stages
- **INPUT**: Receive data from users or systems
- **PARSE**: Extract structure and meaning
- **THINK**: Reasoning and planning
- **DO**: Execute actions and tools
- **REVIEW**: Validate and ensure quality
- **OUTPUT**: Format and deliver results

## Architecture Benefits

**Modular**: Each plugin has one responsibility
**Composable**: Mix and match for any use case
**Testable**: Unit test plugins independently
**Configurable**: Change behavior via YAML
**Reusable**: Share plugins across projects

## Installation

```bash
# Basic installation
pip install entity-core

# With extras
pip install entity-core[dev]  # Development tools
pip install entity-core[all]  # All optional dependencies
```

## Running Examples

Each example can be run directly:
```bash
python examples/hello_agent/hello_agent.py
python examples/tool_usage/calculator_agent.py
python examples/conversation_memory/memory_agent.py
```

## Documentation

Full documentation: [entity-core.readthedocs.io](https://entity-core.readthedocs.io/)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
