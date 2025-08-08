# Getting Started with Entity Framework

## 30-Second Quickstart

Get Entity Framework running in seconds:

```bash
# Install Entity
pip install entity-core

# Run your first agent
python -c "
from entity import Agent
from entity.defaults import load_defaults
import asyncio

async def demo():
    agent = Agent(resources=load_defaults())
    await agent.chat('')  # That's it! Instant intelligent agent!

asyncio.run(demo())
"
```

**🎉 Congratulations!** You just created an intelligent agent with:
- 🧠 Natural language understanding
- 💾 Persistent memory across conversations
- 🔧 Extensible plugin architecture
- 📊 Built-in logging and monitoring

## Progressive Examples - From Hello World to Production

Master Entity Framework through carefully crafted examples that build on each other:

### Level 1: Zero-Config Agent (2 minutes)
```python
from entity import Agent
from entity.defaults import load_defaults

# Instant agent with automatic configuration
agent = Agent(resources=load_defaults())
await agent.chat("")  # Full conversational AI, zero setup
```

### Level 2: Personality via YAML (5 minutes)
```yaml
# config/tutor.yaml
role: |
  You are a helpful Python tutor who explains concepts clearly
  with examples and encouragement.
```

```python
from entity import Agent
agent = Agent.from_config("config/tutor.yaml")
# YAML defines: role="You are a helpful Python tutor"
```

### Level 3: Tools & Capabilities (10 minutes)
```yaml
# config/researcher.yaml
tools:
  web_search: enabled
  calculator: enabled
  file_operations: enabled
```

```python
agent = Agent.from_config("config/researcher.yaml")
response = await agent.chat("Search for Entity Framework benchmarks and calculate the performance improvement")
# YAML enables: web_search, calculator, file_operations
# Agent automatically uses the right tools for the task
```

### Level 4: Multi-Agent Collaboration (15 minutes)
```python
from entity import Agent, AgentOrchestrator

# Create specialized agents
researcher = Agent.from_config("researcher_config.yaml")
writer = Agent.from_config("writer_config.yaml")
reviewer = Agent.from_config("reviewer_config.yaml")

# Orchestrate workflow
orchestrator = AgentOrchestrator([researcher, writer, reviewer])
result = await orchestrator.execute("Write a technical blog post about Entity Framework")
# Researcher gathers info → Writer creates post → Reviewer refines → Final result
```

### Level 5: Production Configuration (Complete system)
```python
from entity import Agent
from entity.monitoring import setup_observability

# Production-ready agent with full observability
agent = Agent.from_config("production_config.yaml")
setup_observability(agent, metrics=True, alerts=True, tracing=True)

# YAML configures: clustering, load balancing, database, monitoring, safety filters
await agent.serve(host="0.0.0.0", port=8000)  # Production API server
```

## Ready for More?

Explore our comprehensive examples:

- [**Hello Agent**](../examples/01_hello_agent/) - Your first zero-config agent
- [**Agent Personality**](../examples/02_agent_personality/) - YAML-driven customization
- [**Tool Usage**](../examples/03_tool_usage/) - Give your agent superpowers
- [**Conversation Memory**](../examples/04_conversation_memory/) - Agents that remember
- [**Streaming Responses**](../examples/05_streaming_responses/) - Real-time interactions

For the complete experience, follow our [5-Minute Quick Start Tutorial](quickstart.md)!
