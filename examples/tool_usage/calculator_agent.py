#!/usr/bin/env python3
"""Calculator Agent - Demonstrates Entity's tool plugin system."""

import asyncio

from entity import Agent
from entity.defaults import load_defaults


async def main():
    """Agent with calculator tool in the DO stage."""

    resources = load_defaults()

    # Configure workflow with calculator tool
    workflow = {
        "input": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
        "parse": ["entity.plugins.defaults.ParsePlugin"],
        "think": ["entity.plugins.defaults.ThinkPlugin"],
        "do": ["entity.plugins.examples.calculator.Calculator"],  # Math tool
        "review": ["entity.plugins.defaults.ReviewPlugin"],
        "output": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
    }

    agent = Agent.from_workflow_dict(workflow, resources=resources)

    print("Calculator Agent ready.")
    print("Try: 42 * 17 + 3.14\n")

    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCalculation complete.")
