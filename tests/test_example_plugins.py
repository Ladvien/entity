from datetime import datetime

import pytest

from entity.core.context import PluginContext
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.pipeline.state import ConversationEntry, PipelineState
from entity.pipeline.stages import PipelineStage
from plugins.examples import InputLogger, MessageParser, ResponseReviewer


@pytest.mark.asyncio
async def test_example_plugins_execute():
    registry = PluginRegistry()
    await registry.register_plugin_for_stage(InputLogger({}), PipelineStage.INPUT)
    await registry.register_plugin_for_stage(MessageParser({}), PipelineStage.PARSE)
    await registry.register_plugin_for_stage(ResponseReviewer({}), PipelineStage.REVIEW)

    caps = SystemRegistries(resources={}, tools=ToolRegistry(), plugins=registry)
    state = PipelineState(
        conversation=[ConversationEntry("Hello badword", "user", datetime.now())],
        pipeline_id="pid",
    )
    ctx = PluginContext(state, caps)

    ctx.set_current_stage(PipelineStage.INPUT)
    ctx.set_current_plugin("InputLogger")
    await InputLogger({}).execute(ctx)
    assert state.stage_results["raw_input"] == "Hello badword"

    ctx.set_current_stage(PipelineStage.PARSE)
    ctx.set_current_plugin("MessageParser")
    await MessageParser({}).execute(ctx)
    assert state.stage_results["parsed_input"] == "hello badword"

    state.response = "hello badword"
    ctx.set_current_stage(PipelineStage.REVIEW)
    ctx.set_current_plugin("ResponseReviewer")
    await ResponseReviewer({}).execute(ctx)
    assert state.response == "hello ***"
