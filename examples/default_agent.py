#!/usr/bin/env python3
"""Default Agent - Demonstrates Entity framework with automatic resource setup.

This example shows the simplest way to use Entity framework:
- Uses default plugins and workflow
- Automatic resource initialization with load_defaults()
- Zero-configuration setup
- Interactive chat interface

For more advanced plugin-based examples, see examples/simple_chat/
"""

import asyncio
import os

from entity import Agent
from entity.defaults import load_defaults


async def main() -> None:
    """Run a minimal agent using Entity's automatic defaults."""

    print("🤖 Default Entity Agent")
    print("=" * 30)
    print("This example uses Entity's default plugins and automatic resource setup.")
    print("For custom plugin examples, see: examples/simple_chat/")
    print()

    try:
        # Optional: Configure logging
        os.environ.setdefault("ENTITY_JSON_LOGS", "0")
        os.environ.setdefault("ENTITY_LOG_LEVEL", "info")

        # Load resources with automatic defaults
        # This sets up LLM, Memory, FileStorage, Logging automatically
        resources = load_defaults()

        # Create agent with default workflow and resources
        # The default workflow uses Entity's built-in plugins for basic chat
        agent = Agent(resources=resources)

        print("✅ Agent initialized with default resources and workflow")
        print("💬 Starting interactive chat (press Ctrl+C to exit)")
        print("-" * 50)

        # Start interactive chat session
        # Empty string triggers Entity's interactive CLI adapter
        await agent.chat("")

    except Exception as exc:
        print(f"❌ Failed to initialize agent: {exc}")
        print()
        print("Common issues:")
        print("- No LLM available (install Ollama or configure API keys)")
        print("- Missing dependencies (run: pip install entity-core)")
        print("- Resource initialization failed")
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("This is a minimal Entity framework example.")
        print("For more advanced usage, see: examples/simple_chat/")
