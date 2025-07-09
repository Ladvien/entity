"""Run a simple HTTP server using the Entity framework.

Run with ``python -m examples.servers.http_server`` or install the package in
editable mode.
"""

from __future__ import annotations


from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

import asyncio
from typing import Any

from pipeline import PipelineManager
from pipeline.initializer import SystemInitializer
from pipeline.resources.memory import Memory
from plugins.builtin.adapters.http import HTTPAdapter, MessageRequest


async def main() -> None:
    initializer = SystemInitializer.from_yaml("config/dev.yaml")
    registries = await initializer.initialize()
    pipeline_manager = PipelineManager(registries)
    memory: Memory = registries.resources.get("memory")  # type: ignore[arg-type]
    conversation_manager = memory.start_conversation(registries, pipeline_manager)
    adapter = HTTPAdapter(pipeline_manager, {"host": "127.0.0.1", "port": 8000})

    @adapter.app.post("/conversation")
    async def conversation(req: MessageRequest) -> dict[str, Any]:
        return await conversation_manager.process_request(req.message)

    await adapter.serve(registries)


if __name__ == "__main__":
    asyncio.run(main())
