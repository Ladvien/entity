from datetime import datetime
import pytest

from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.state import ConversationEntry
from entity.pipeline.pipeline import execute_pipeline
from entity.pipeline.state import PipelineState
from entity.pipeline.stages import PipelineStage


class StoreOnce(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        if context._state.iteration == 1:
            await context.think("msg", context.conversation()[-1].content)


class DelayedEcho(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        if context._state.iteration < 2:
            return
        msg = await context.reflect("msg")
        context.say(msg)


@pytest.mark.asyncio
async def test_stage_results_persist_between_iterations():
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(StoreOnce({}), PipelineStage.THINK, "store")
    await plugins.register_plugin_for_stage(
        DelayedEcho({}), PipelineStage.OUTPUT, "echo"
    )
    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="test",
    )
    result = await execute_pipeline(
        "hi", regs, state=state, max_iterations=3, workflow=None
    )
    assert result == "hi"
    assert state.iteration == 2
