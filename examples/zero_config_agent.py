from __future__ import annotations

"""Run a minimal agent using automatic defaults.

All required resources are prepared on first run. If initialization fails,
an error message is printed and the program exits.
"""

import asyncio
import os

from entity import Agent
from entity.defaults import load_defaults


async def main() -> None:
    try:
        os.environ.setdefault("ENTITY_AUTO_INSTALL_OLLAMA", "0")
        # Write JSON logs to ``zero_agent.log``
        os.environ.setdefault("ENTITY_JSON_LOGS", "1")
        os.environ.setdefault("ENTITY_LOG_FILE", "zero_agent.log")
        resources = load_defaults()
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
