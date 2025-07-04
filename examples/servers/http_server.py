"""Run a simple HTTP server using the Entity framework."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

import asyncio
from typing import Any

from pipeline import ConversationManager, PipelineManager
from pipeline.initializer import SystemInitializer
from plugins.adapters.http import HTTPAdapter, MessageRequest


async def main() -> None:
    initializer = SystemInitializer.from_yaml("config/dev.yaml")
    registries = await initializer.initialize()
    pipeline_manager = PipelineManager(registries)
    conversation_manager = ConversationManager(registries, pipeline_manager)
    adapter = HTTPAdapter(pipeline_manager, {"host": "127.0.0.1", "port": 8000})

    @adapter.app.post("/conversation")
    async def conversation(req: MessageRequest) -> dict[str, Any]:
        return await conversation_manager.process_request(req.message)

    await adapter.serve(registries)


if __name__ == "__main__":
    asyncio.run(main())
