from __future__ import annotations

import asyncio
from typing import Any
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from user_plugins.tools.calculator_tool import CalculatorTool
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


class EchoLLMResource(ResourcePlugin):
    """LLM resource that echoes the prompt."""

    async def generate(self, prompt: str) -> Any:
        return {"content": prompt}


class ReActPrompt(PromptPlugin):
    """Very small ReAct style prompt."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        question = next(
            (e.content for e in context.conversation() if e.role == "user"), ""
        )
        tool_result = await context.tool_use("calc", expression="2+2")
        context.say(f"Thinking about {question} using tool result {tool_result}")


class FinalResponder(PromptPlugin):
    """Return the last assistant message."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        assistant = [e.content for e in context.conversation() if e.role == "assistant"]
        context.set_response(assistant[-1] if assistant else "")


async def main() -> None:
    resources = ResourceContainer()
    db = DuckDBDatabaseResource({"path": "./agent.duckdb"})
    memory = Memory(database=db)
    await db.initialize()
    await resources.add("database", db)
    await resources.add("memory", memory)
    await resources.add("llm", EchoLLMResource({}))

    tools = ToolRegistry()
    await tools.add("calc", CalculatorTool())

    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(
        ReActPrompt({"max_steps": 2}), PipelineStage.THINK, "react"
    )
    await plugins.register_plugin_for_stage(
        FinalResponder(), PipelineStage.DELIVER, "final"
    )

    caps = SystemRegistries(resources=resources, tools=tools, plugins=plugins)

    state = PipelineState(
        conversation=[
            ConversationEntry(
                content="What is 2 + 2?", role="user", timestamp=datetime.now()
            )
        ],
        pipeline_id=generate_pipeline_id(),
    )
    result: dict[str, Any] = await execute_pipeline("What is 2 + 2?", caps, state=state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
