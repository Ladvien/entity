#!/usr/bin/env python3
"""
02 - Agent with Personality: Customizable AI Assistant

This example demonstrates how to create agents with specific personalities,
expertise, and communication styles using Entity's configuration system.

What this demonstrates:
- Role-based agents with specific personalities
- YAML configuration for behavior customization
- Communication styles (professional, casual, educational)
- Domain expertise specialization
- Configuration-driven development (no code changes needed)
"""

import asyncio
from pathlib import Path

from entity import Agent


async def main():
    """Run an agent with a custom personality."""

    print("🎭 Entity Agent with Custom Personality")
    print("=" * 42)
    print()
    print("This example demonstrates how Entity agents can have:")
    print("• Specific roles and expertise")
    print("• Custom communication styles")
    print("• Tailored behavior patterns")
    print("• Domain-specific knowledge focus")
    print()

    # Configuration file path
    config_path = Path(__file__).parent / "python_tutor.yaml"

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print("💡 Make sure python_tutor.yaml is in the same directory")
        print()
        print("🔧 You can create different personality configs:")
        print("   • python_tutor.yaml - Patient programming teacher")
        print("   • creative_writer.yaml - Imaginative writing partner")
        print("   • business_consultant.yaml - Professional advisor")
        return

    try:
        # Load agent from configuration
        # The YAML file defines the agent's personality and behavior
        print("⚙️  Loading agent personality from configuration...")
        agent = Agent.from_config(str(config_path))

        print("✅ Python Tutor Agent loaded!")
        print("🐍 Specialized in: Python programming education")
        print("🎯 Communication style: Patient and educational")
        print("📚 Focus: Teaching with examples and best practices")
        print()
        print("💬 Try asking about:")
        print("   • 'Explain Python decorators'")
        print("   • 'What are list comprehensions?'")
        print("   • 'Show me a simple web scraping example'")
        print("   • 'How do I handle exceptions properly?'")
        print("   • 'What's the difference between lists and tuples?'")
        print()
        print("💡 The agent's personality is defined entirely in the YAML file!")
        print("   Change the config → Restart → New personality (no code changes!)")
        print()
        print("🚀 Starting your Python tutoring session...")
        print("=" * 42)

        # Start interactive chat
        await agent.chat("")

    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        print("📁 Please ensure the YAML config file exists in this directory")

    except Exception as e:
        print(f"❌ Error loading agent: {e}")
        print("🔧 Common issues:")
        print("   • Invalid YAML syntax in config file")
        print("   • Missing Entity framework installation")
        print("   • LLM service not available (Ollama/API)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Happy coding! Your Python tutor is always here to help.")
        print("🎯 Want a different personality? Edit the YAML config file!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("📚 For help, visit: https://entity-core.readthedocs.io/")
