#!/usr/bin/env python3
"""Simple Chat Agent - Demonstrates proper Entity framework plugin architecture.

This example shows how to build an Entity agent using the framework's plugin system:
- Plugins inherit from Entity base classes (InputAdapterPlugin, PromptPlugin, etc.)
- Workflow defined in YAML configuration
- Uses Entity's 6-stage pipeline: INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
- Demonstrates inter-plugin communication via context.remember/recall
- Shows proper resource dependencies and configuration validation

Usage:
    python chat_agent.py
"""

import asyncio
from pathlib import Path

from entity import Agent


async def main():
    """Run the simple chat agent using Entity's plugin architecture."""

    # Create agent from workflow configuration
    # This is the proper Entity pattern - configuration defines the plugins and workflow
    config_path = Path(__file__).parent / "chat_config.yaml"

    if config_path.exists():
        # Load agent with plugin-based workflow
        agent = Agent.from_config(str(config_path))
        print("🤖 Simple Chat Agent (Entity Framework)")
        print("=" * 40)
        print("Type '/help' for commands or '/quit' to exit")
        print()

        # Start interactive chat session
        # The agent will use the plugin pipeline defined in chat_config.yaml
        await agent.chat("")

    else:
        print(f"❌ Configuration file not found: {config_path}")
        print("Make sure chat_config.yaml exists in the same directory.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nThis example demonstrates Entity's plugin architecture.")
        print("Make sure you have Entity framework installed and configured.")
