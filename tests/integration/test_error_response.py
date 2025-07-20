import pytest
from datetime import datetime

from entity.core.context import PluginContext
from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.state import ConversationEntry, PipelineState
from entity.pipeline.pipeline import execute_pipeline
from entity.pipeline.stages import PipelineStage
from plugins.builtin.basic_error_handler import BasicErrorHandler


class BoomPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        raise RuntimeError("boom")


class BasicErrorResponder(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        if context.response is not None:
            context.say(context.response)


@pytest.mark.asyncio
async def test_error_handled_by_responder():
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(BoomPlugin({}), PipelineStage.THINK)
    await plugins.register_plugin_for_stage(BasicErrorHandler({}), PipelineStage.ERROR)
    await plugins.register_plugin_for_stage(
        BasicErrorResponder({}), PipelineStage.OUTPUT
    )

    regs = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=plugins)
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    result = await execute_pipeline("hi", regs, state=state)

    expected = {
        "error": "boom",
        "message": "Unable to process request",
        "error_id": "pid",
        "plugin": "BoomPlugin",
        "stage": "PipelineStage.THINK",
        "type": "plugin_error",
    }

    assert result == expected
    assert [e.role for e in state.conversation] == ["user", "assistant"]
    assert state.conversation[-1].content == expected
