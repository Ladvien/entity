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

from entity.plugins.prompts.plan_and_execute import PlanAndExecutePrompt


class EchoLLMResource(ResourcePlugin):
    async def generate(self, prompt: str) -> Any:
        if "Break the goal" in prompt:
            return {"content": "Step one\nStep two"}
        if "Execute step" in prompt:
            step = prompt.split(":", 1)[1].strip()
            return {"content": f"Executed {step}"}
        return {"content": prompt}


class FinalResponder(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        assistant = [e.content for e in context.conversation() if e.role == "assistant"]
        context.say(assistant[-1] if assistant else "")


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
        PlanAndExecutePrompt({}), PipelineStage.THINK, "planner"
    )
    await plugins.register_plugin_for_stage(
        FinalResponder(), PipelineStage.OUTPUT, "final"
    )

    caps = SystemRegistries(resources=resources, tools=ToolRegistry(), plugins=plugins)

    state = PipelineState(
        conversation=[
            ConversationEntry(
                content="Build a shed", role="user", timestamp=datetime.now()
            )
        ],
        pipeline_id=generate_pipeline_id(),
    )
    result: dict[str, Any] = await execute_pipeline("Build a shed", caps, state=state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
