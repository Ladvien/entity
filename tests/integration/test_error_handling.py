import pytest

from datetime import datetime

from entity.core.context import PluginContext
from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.state import ConversationEntry, PipelineState
from entity.pipeline.pipeline import execute_pipeline
from entity.pipeline.stages import PipelineStage


class FailingPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        raise RuntimeError("fail")


class CaptureErrorPlugin(Plugin):
    stages = [PipelineStage.ERROR]

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.called = False

    async def _execute_impl(self, context: PluginContext) -> None:
        self.called = True
        context._state.response = "error handled"


class SkippedPlugin(Plugin):
    stages = [PipelineStage.THINK]

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.executed = False

    async def _execute_impl(self, context: PluginContext) -> None:
        self.executed = True


class SayWrongStagePlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        context.say("nope")


@pytest.mark.asyncio
async def test_plugin_failure_triggers_error_stage():
    plugins = PluginRegistry()
    error_plugin = CaptureErrorPlugin()
    await plugins.register_plugin_for_stage(
        FailingPlugin({}), PipelineStage.THINK, "fail"
    )
    await plugins.register_plugin_for_stage(error_plugin, PipelineStage.ERROR, "err")

    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    result = await execute_pipeline("hi", regs, state=state)
    assert result == "error handled"
    assert error_plugin.called is True


@pytest.mark.asyncio
async def test_stage_stops_after_failure():
    plugins = PluginRegistry()
    error_plugin = CaptureErrorPlugin()
    skipped = SkippedPlugin()
    await plugins.register_plugin_for_stage(
        FailingPlugin({}), PipelineStage.THINK, "fail"
    )
    await plugins.register_plugin_for_stage(skipped, PipelineStage.THINK, "skip")
    await plugins.register_plugin_for_stage(error_plugin, PipelineStage.ERROR, "err")

    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    result = await execute_pipeline("hi", regs, state=state)
    assert result == "error handled"
    assert error_plugin.called is True
    assert skipped.executed is False


@pytest.mark.asyncio
async def test_say_misuse_triggers_plugin_context_error():
    plugins = PluginRegistry()
    error_plugin = CaptureErrorPlugin()
    await plugins.register_plugin_for_stage(
        SayWrongStagePlugin({}), PipelineStage.THINK, "bad"
    )
    await plugins.register_plugin_for_stage(error_plugin, PipelineStage.ERROR, "err")

    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    result = await execute_pipeline("hi", regs, state=state)
    assert result == "error handled"
    assert error_plugin.called is True
    assert state.failure_info is not None
    assert state.failure_info.error_type == "PluginContextError"
