#!/usr/bin/env python3
"""Code Review Agent - Demonstrates Entity framework plugin architecture for code analysis.

This example shows how to build specialized Entity agents using plugins:
- Custom input processing for code files and directories
- Plugin-based workflow for code analysis
- Proper resource management and configuration

Usage:
    python code_reviewer.py

Then provide a file path, directory, or code to review.
"""

import asyncio
from pathlib import Path

from entity import Agent


async def main():
    """Run the code review agent using Entity's plugin architecture."""

    print("🔍 Code Review Agent (Entity Framework)")
    print("=" * 45)
    print("This example demonstrates plugin-based code analysis.")
    print()
    print("You can:")
    print("- Provide a file path: ./my_script.py")
    print("- Provide a directory: ./src")
    print("- Paste code directly")
    print("- Provide git diff content")
    print()

    # Create agent from workflow configuration
    config_path = Path(__file__).parent / "reviewer_config.yaml"

    if config_path.exists():
        # Load agent with plugin-based workflow
        agent = Agent.from_config(str(config_path))

        print("✅ Code reviewer initialized with plugin workflow")
        print("💬 Enter code, file path, or directory to review:")
        print("-" * 50)

        # Start interactive review session
        await agent.chat("")

    else:
        print(f"❌ Configuration file not found: {config_path}")
        print("Make sure reviewer_config.yaml exists in the same directory.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Code review session ended!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(
            "\nThis example demonstrates Entity's plugin architecture for code analysis."
        )
        print("Make sure you have Entity framework installed and configured.")
