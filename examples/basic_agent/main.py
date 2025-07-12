from __future__ import annotations

import asyncio
from typing import Any
from pathlib import Path
import sys

from entity.core.plugins import PromptPlugin
from entity.core.context import PluginContext
from pipeline.stages import PipelineStage
from datetime import datetime

from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.resources.memory import Memory
from pipeline.pipeline import execute_pipeline, generate_pipeline_id

sys.path.append(str(Path(__file__).resolve().parents[2]))
from pipeline.state import ConversationEntry, PipelineState


class EchoPrompt(PromptPlugin):
    """Return the last user message."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        last_message = ""
        for entry in reversed(context.conversation()):
            if entry.role == "user":
                last_message = entry.content
                break
        context.set_response(f"You said: {last_message}")


async def main() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(EchoPrompt(), PipelineStage.DELIVER, "echo")

    resources = ResourceContainer()
    resources.register(
        "database",
        DuckDBInfrastructure,
        {"path": "./agent.duckdb"},
        layer=1,
    )
    resources.register("memory", Memory, {}, layer=3)
    await resources.build_all()

    caps = SystemRegistries(resources=resources, tools=ToolRegistry(), plugins=plugins)

    state = PipelineState(
        conversation=[
            ConversationEntry(content="Hello", role="user", timestamp=datetime.now())
        ],
        pipeline_id=generate_pipeline_id(),
    )
    result: dict[str, Any] = await execute_pipeline("Hello", caps, state=state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
