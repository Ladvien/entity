#!/usr/bin/env python3
"""Hello Agent with custom workflow - Showcasing Entity's plugin pipeline."""

import asyncio

from entity import Agent
from entity.defaults import load_defaults


async def main():
    """Create an agent with a custom workflow pipeline."""

    resources = load_defaults()

    # Define a custom workflow using Entity's 6-stage pipeline
    workflow = {
        "input": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
        "parse": ["entity.plugins.defaults.ParsePlugin"],
        "think": ["entity.plugins.prompt.PromptPlugin"],
        "do": ["entity.plugins.defaults.DoPlugin"],
        "review": ["entity.plugins.defaults.ReviewPlugin"],
        "output": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
    }

    agent = Agent.from_workflow_dict(workflow, resources=resources)

    print("Enhanced Entity Agent with custom workflow.\n")

    # Interactive session with rich CLI interface
    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSession ended.")
