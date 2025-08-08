#!/usr/bin/env python3
"""
01 - Hello Agent: The Simplest Possible Entity Agent

This is your introduction to Entity Framework - a complete AI agent
in just a few lines of code with zero configuration required.

What this demonstrates:
- Zero-config agent creation using Entity defaults
- Automatic LLM setup (Ollama or cloud APIs)
- Built-in memory that persists between conversations
- Interactive chat interface

Run this example to see how easy it is to create intelligent agents with Entity!
"""

import asyncio

from entity import Agent
from entity.defaults import load_defaults


async def main():
    """Create and run your first Entity agent."""

    print("🤖 Hello Agent - Your First Entity Framework Agent")
    print("=" * 55)
    print()
    print("This example demonstrates the simplest possible Entity agent.")
    print("No configuration files, no complex setup - just pure simplicity!")
    print()

    try:
        print("⚙️  Setting up your agent...")

        # Load default resources (LLM, Memory, Logging, Storage)
        # This single call sets up everything you need:
        # - Local LLM (Ollama) or cloud API connection
        # - Persistent memory with DuckDB database
        # - Structured logging for debugging
        # - File storage for agent data
        resources = load_defaults()

        # Create an agent with these resources
        # The agent is now ready to chat intelligently!
        agent = Agent(resources=resources)

        print("✅ Agent created successfully!")
        print()
        print("🎯 What your agent can do:")
        print("   • Answer questions intelligently")
        print("   • Remember conversation history")
        print("   • Maintain context across sessions")
        print("   • Handle complex multi-turn dialogues")
        print()
        print("💬 Starting interactive chat...")
        print("   Type your messages and press Enter")
        print("   Type 'quit', 'exit', or Ctrl+C to end the session")
        print()
        print(
            "🎉 Try saying: 'Hello! What's your name?' or 'Tell me about Entity Framework'"
        )
        print("=" * 55)

        # Start interactive chat session
        # Empty string triggers Entity's built-in interactive mode
        # This creates a full conversational interface automatically
        await agent.chat("")

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print()
        print("🔧 To fix this, run: pip install entity-core")

    except Exception as e:
        print(f"❌ Error setting up agent: {e}")
        print()
        print("🔧 Common solutions:")
        print("   • Make sure Ollama is running: ollama serve")
        print("   • Or set an API key: export OPENAI_API_KEY='your-key'")
        print("   • Check the troubleshooting guide in README.md")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
        print("👋 Thanks for trying Entity Framework!")
        print("🚀 Ready to build more complex agents?")
        print("   Check out the other examples in this directory!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("📚 For help, visit: https://entity-core.readthedocs.io/")
