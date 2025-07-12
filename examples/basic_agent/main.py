from __future__ import annotations

import asyncio
from typing import Any
from pathlib import Path
import sys

base = Path(__file__).resolve().parents[2]
sys.path.append(str(base / "src"))
sys.path.append(str(base))
# ruff: noqa: E402

from entity.core.plugins import PromptPlugin
from entity.core.context import PluginContext
from entity.core.stages import PipelineStage
from datetime import datetime

from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.resources.memory import Memory
from entity.resources.logging import LoggingResource
from entity.pipeline.pipeline import execute_pipeline, generate_pipeline_id
from entity.pipeline.state import ConversationEntry, PipelineState


class EchoPrompt(PromptPlugin):
    """Return the last user message."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        last_message = ""
        for entry in reversed(context.conversation()):
            if entry.role == "user":
                last_message = entry.content
                break
        context.say(f"You said: {last_message}")


async def main() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(EchoPrompt(), PipelineStage.OUTPUT, "echo")

    resources = ResourceContainer()
    db = DuckDBInfrastructure({"path": "./agent.duckdb"})
    memory = Memory(config={})
    memory.database = db
    await db.initialize()
    await resources.add("database", db)
    await resources.add("memory", memory)
    resources.register("logging", LoggingResource, {}, layer=3)
    await resources.build_all()
    logger: LoggingResource = resources.get("logging")  # type: ignore[assignment]

    caps = SystemRegistries(resources=resources, tools=ToolRegistry(), plugins=plugins)

    state = PipelineState(
        conversation=[
            ConversationEntry(content="Hello", role="user", timestamp=datetime.now())
        ],
        pipeline_id=generate_pipeline_id(),
    )
    result: dict[str, Any] = await execute_pipeline("Hello", caps, state=state)
    await logger.log(
        "info", "pipeline finished", component="pipeline", pipeline_id=state.pipeline_id
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
