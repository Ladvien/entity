from datetime import datetime

import pytest

from entity.plugins.prompts.plan_and_execute import PlanAndExecutePrompt
from entity.core.context import PluginContext
from entity.core.registries import (
    SystemRegistries,
    PluginRegistry,
    ToolRegistry,
)
from entity.core.resources.container import ResourceContainer
from entity.core.state import ConversationEntry, LLMResponse
from pipeline.state import PipelineState
from entity.resources.interfaces.llm import LLMResource
from pipeline.stages import PipelineStage


class DummyLLMProvider(LLMResource):
    async def generate(self, prompt: str) -> LLMResponse:
        if "Break the goal" in prompt:
            return LLMResponse(content="Step one\nStep two")
        return LLMResponse(content=f"Executed {prompt.split(':', 1)[1].strip()}")


@pytest.mark.asyncio
async def test_plan_and_execute_prompt() -> None:
    llm = DummyLLMProvider({})
    container = ResourceContainer()
    await container.add("llm", llm)

    plugins = PluginRegistry()
    regs = SystemRegistries(resources=container, tools=ToolRegistry(), plugins=plugins)

    state = PipelineState(
        conversation=[ConversationEntry("Do something", "user", datetime.now())],
        pipeline_id="pid",
    )
    ctx = PluginContext(state, regs)
    ctx.set_current_stage(PipelineStage.THINK)
    plugin = PlanAndExecutePrompt({})
    await plugin.execute(ctx)
    assert await ctx.reflect("plan") == ["Step one", "Step two"]
    assert await ctx.reflect("completed") is True
