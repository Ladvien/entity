#!/usr/bin/env python3
"""Agent with personality - Configuration-driven behavior customization."""

import asyncio
import sys
from pathlib import Path

from entity import Agent


async def main():
    """Run an agent with a custom personality from YAML configuration."""

    # Use provided config or default to python_tutor
    config_file = sys.argv[1] if len(sys.argv) > 1 else "python_tutor.yaml"
    config_path = Path(__file__).parent / config_file

    if not config_path.exists():
        print(f"Config not found: {config_path}")
        print("\nAvailable personalities:")
        print("  python_tutor.yaml - Patient programming teacher")
        print("  creative_writer.yaml - Imaginative writing partner")
        print("  business_consultant.yaml - Professional advisor")
        return

    # Load agent with personality from YAML
    agent = Agent.from_config(str(config_path))

    print(f"Loaded: {config_path.stem}")
    print("Chat started. Type 'exit' to quit.\n")

    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSession ended.")
