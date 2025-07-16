from datetime import datetime
import pytest

from entity.core.context import PluginContext
from entity.core.plugins import PromptPlugin
from entity.core.registries import (
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from entity.core.state import ConversationEntry
from entity.pipeline.state import PipelineState
from entity.pipeline.stages import PipelineStage
from entity.pipeline.pipeline import execute_pipeline
from entity.pipeline.errors import PluginContextError
from entity.core.resources.container import ResourceContainer


def make_context(stage: PipelineStage) -> PluginContext:
    state = PipelineState(conversation=[])
    container = ResourceContainer()
    ctx = PluginContext(
        state,
        SystemRegistries(
            resources=container, tools=ToolRegistry(), plugins=PluginRegistry()
        ),
    )
    ctx.set_current_stage(stage)
    ctx.set_current_plugin("test")
    return ctx


def test_say_only_output_stage() -> None:
    ctx = make_context(PipelineStage.THINK)
    with pytest.raises(PluginContextError):
        ctx.say("hi")


class Thinker(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        await context.think("data", "x")


class Responder(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        val = await context.reflect("data")
        context.say(f"final:{val}")


class SilentOutput(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        pass


@pytest.mark.asyncio
async def test_pipeline_terminates_after_say() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(Thinker({}), PipelineStage.THINK, "t")
    await plugins.register_plugin_for_stage(Responder({}), PipelineStage.OUTPUT, "r")
    regs = SystemRegistries(
        resources=ResourceContainer(), tools=ToolRegistry(), plugins=plugins
    )
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="test",
    )
    result = await execute_pipeline("hi", regs, state=state, workflow=None)
    assert result == "final:x"


@pytest.mark.asyncio
async def test_pipeline_max_iteration_error() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(Thinker({}), PipelineStage.THINK, "t")
    await plugins.register_plugin_for_stage(SilentOutput({}), PipelineStage.OUTPUT, "o")
    regs = SystemRegistries(
        resources=ResourceContainer(), tools=ToolRegistry(), plugins=plugins
    )
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    await execute_pipeline("hi", regs, state=state, max_iterations=2, workflow=None)
    assert state.failure_info and state.failure_info.error_type == "max_iterations"
