from __future__ import annotations

import asyncio
from typing import Any
from pathlib import Path
import sys

from entity.core.plugins import PromptPlugin, ResourcePlugin
from entity.core.context import PluginContext
from pipeline.stages import PipelineStage
from datetime import datetime

from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.resources.memory import Memory
from pipeline.pipeline import execute_pipeline, generate_pipeline_id
from pipeline.state import ConversationEntry, PipelineState

sys.path.append(str(Path(__file__).resolve().parents[2]))


class EchoLLMResource(ResourcePlugin):
    """LLM resource that echoes the prompt."""

    async def generate(self, prompt: str) -> Any:
        return {"content": prompt}


class ChainOfThoughtPrompt(PromptPlugin):
    """Simple reasoning plugin."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        user = next((e.content for e in context.conversation() if e.role == "user"), "")
        await context.think("thought", f"Thought about: {user}")


class FinalResponder(PromptPlugin):
    """Send the last assistant message as the response."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        thought = await context.reflect("thought")
        context.say(thought or "")


async def main() -> None:
    resources = ResourceContainer()
    db = DuckDBInfrastructure({"path": "./agent.duckdb"})
    memory = Memory(config={})
    memory.database = db
    await db.initialize()
    await resources.add("database", db)
    await resources.add("memory", memory)
    await resources.add("llm", EchoLLMResource({}))

    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(
        ChainOfThoughtPrompt({"max_steps": 1}), PipelineStage.THINK, "cot"
    )
    await plugins.register_plugin_for_stage(
        FinalResponder(), PipelineStage.OUTPUT, "final"
    )

    caps = SystemRegistries(resources=resources, tools=ToolRegistry(), plugins=plugins)

    state = PipelineState(
        conversation=[
            ConversationEntry(
                content="Explain the sky", role="user", timestamp=datetime.now()
            )
        ],
        pipeline_id=generate_pipeline_id(),
    )
    result: dict[str, Any] = await execute_pipeline(
        "Explain the sky", caps, state=state
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
