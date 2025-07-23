from __future__ import annotations

import asyncio

from ..core.agent import Agent
from ..plugins.defaults import (
    ParsePlugin,
    ThinkPlugin,
    DoPlugin,
    ReviewPlugin,
)
from .ent_cli_adapter import EntCLIAdapter


async def _run() -> None:
    workflow = [
        EntCLIAdapter,
        ParsePlugin,
        ThinkPlugin,
        DoPlugin,
        ReviewPlugin,
        EntCLIAdapter,
    ]
    agent = Agent(workflow=workflow)
    await agent.chat("")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
