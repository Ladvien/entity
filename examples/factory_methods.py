"""Demonstrate Agent factory helpers.

Resources are created with :func:`load_defaults`. Any initialization
errors are printed and the example exits cleanly.
"""

from entity.core.agent import Agent
from entity.defaults import load_defaults
import os


try:
    # Store logs for inspection
    os.environ.setdefault("ENTITY_LOG_FILE", "factory.log")
    default_resources = load_defaults()
except Exception as exc:  # pragma: no cover - example runtime guard
    print(f"Failed to initialize resources: {exc}")
    raise SystemExit(1)

# Build from a workflow template
agent_from_template = Agent.from_workflow("basic", resources=default_resources)

# Build from a dictionary mapping stages to plugins
agent_from_dict = Agent.from_workflow_dict(
    {
        "think": ["entity.plugins.defaults.ThinkPlugin"],
        "output": ["entity.plugins.defaults.OutputPlugin"],
    },
    resources=default_resources,
)

# Build from a configuration file
agent_from_config = Agent.from_config(
    "examples/basic_config.yaml", resources=default_resources
)

print(agent_from_template, agent_from_dict, agent_from_config)
