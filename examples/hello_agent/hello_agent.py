#!/usr/bin/env python3
"""Hello Agent - The simplest Entity agent with zero configuration."""

import asyncio

from entity import Agent
from entity.defaults import load_defaults


async def main():
    """Create and run a zero-config Entity agent."""

    # Load default resources and create agent - that's it!
    resources = load_defaults()
    agent = Agent(resources=resources)

    print("Entity Agent ready. Type 'exit' to quit.\n")

    # Start interactive chat with Entity's built-in CLI
    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
