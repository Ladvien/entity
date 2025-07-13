from datetime import datetime
import pytest

from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.pipeline.stages import PipelineStage
from entity.pipeline.state import PipelineState, ConversationEntry
from entity.pipeline.pipeline import execute_pipeline


class Counter(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context) -> None:
        count = await context.reflect("count", 0)
        await context.think("count", count + 1)


class TerminateOnThree(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context) -> None:
        count = await context.reflect("count", 0)
        if count >= 3:
            context.say(str(count))


class EchoFoo(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context) -> None:
        val = await context.reflect("foo", "missing")
        context.say(val)


@pytest.mark.asyncio
async def test_thoughts_accumulate_across_iterations() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(Counter({}), PipelineStage.THINK)
    await plugins.register_plugin_for_stage(TerminateOnThree({}), PipelineStage.OUTPUT)
    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    result = await execute_pipeline(
        "hi", regs, state=state, workflow=None, max_iterations=5
    )
    assert result == "3"
    assert state.iteration == 3
    assert state.stage_results == {}
    assert state.temporary_thoughts == {}


@pytest.mark.asyncio
async def test_thoughts_cleared_between_runs() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(Counter({}), PipelineStage.THINK)
    await plugins.register_plugin_for_stage(TerminateOnThree({}), PipelineStage.OUTPUT)
    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    await execute_pipeline("hi", regs, state=state, workflow=None, max_iterations=5)
    assert state.stage_results == {}

    state.conversation.append(ConversationEntry("again", "user", datetime.now()))
    state.response = None
    state.failure_info = None
    state.iteration = 0
    state.last_completed_stage = None

    result = await execute_pipeline(
        "", regs, state=state, workflow=None, max_iterations=5
    )
    assert result == "3"
    assert state.iteration == 3
    assert state.stage_results == {}
    assert state.temporary_thoughts == {}


@pytest.mark.asyncio
async def test_preexisting_thoughts_available_at_start() -> None:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(EchoFoo({}), PipelineStage.OUTPUT)
    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
        stage_results={"foo": "bar"},
    )
    result = await execute_pipeline(
        "hi", regs, state=state, workflow=None, max_iterations=1
    )
    assert result == "bar"
    assert state.stage_results == {}
    assert state.temporary_thoughts == {}
