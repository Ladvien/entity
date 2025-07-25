"""Demonstrate Agent factory helpers.

Start the service stack before running:

```
docker compose up -d
```
"""

from entity.core.agent import Agent


# Build from a workflow template
agent_from_template = Agent.from_workflow("basic")

# Build from a dictionary mapping stages to plugins
agent_from_dict = Agent.from_workflow_dict(
    {
        "think": ["entity.plugins.defaults.ThinkPlugin"],
        "output": ["entity.plugins.defaults.OutputPlugin"],
    }
)

# Build from a configuration file
agent_from_config = Agent.from_config("examples/basic_config.yaml")

print(agent_from_template, agent_from_dict, agent_from_config)
