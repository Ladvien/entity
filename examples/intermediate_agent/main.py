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
from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource
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
        context.say(f"Thought about: {user}")


class FinalResponder(PromptPlugin):
    """Send the last assistant message as the response."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        assistant_messages = [
            e.content for e in context.conversation() if e.role == "assistant"
        ]
        context.set_response(assistant_messages[-1] if assistant_messages else "")


async def main() -> None:
    resources = ResourceContainer()
    Memory.dependencies = ["database"]
    resources.register("database", DuckDBDatabaseResource, {"path": "./agent.duckdb"})
    resources.register("memory", Memory, {})
    resources.register("llm", EchoLLMResource, {})
    await resources.build_all()

    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(
        ChainOfThoughtPrompt({"max_steps": 1}), PipelineStage.THINK, "cot"
    )
    await plugins.register_plugin_for_stage(
        FinalResponder(), PipelineStage.DELIVER, "final"
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
