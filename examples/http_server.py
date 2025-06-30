"""Run a simple HTTP server using the Entity framework."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import asyncio
from typing import Any

from entity import Agent
from pipeline import ConversationManager, PipelineManager
from pipeline.adapters.http import HTTPAdapter, MessageRequest


async def main() -> None:
    agent = Agent({"server": {"host": "127.0.0.1", "port": 8000}})  # type: ignore[arg-type]
    await agent._ensure_initialized()
    registries = agent._registries
    if registries is None:
        raise RuntimeError("System not initialized")

    pipeline_manager = PipelineManager(registries)
    conversation_manager = ConversationManager(registries, pipeline_manager)
    adapter = HTTPAdapter(pipeline_manager, agent.config.get("server", {}))

    @adapter.app.post("/conversation")
    async def conversation(req: MessageRequest) -> dict[str, Any]:
        return await conversation_manager.process_request(req.message)

    await adapter.serve(registries)


if __name__ == "__main__":
    asyncio.run(main())
