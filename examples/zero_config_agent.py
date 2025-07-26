from __future__ import annotations

"""Run a minimal agent using automatic defaults.

All required resources are prepared on first run. If initialization fails,
an error message is printed and the program exits.
"""

import asyncio

from entity import Agent
from entity.defaults import DefaultConfig, load_defaults


async def main() -> None:
    try:
        resources = load_defaults(DefaultConfig(auto_install_ollama=False))
    except Exception as exc:  # pragma: no cover - example runtime guard
        print(f"Failed to initialize resources: {exc}")
        return

    agent = Agent(resources=resources)
    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
