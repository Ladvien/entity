import asyncio
from datetime import datetime

from pipeline import (
    PluginRegistry,
    PipelineStage,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from entity.core.resources.container import ResourceContainer
from entity.core.state import ConversationEntry
from pipeline.state import PipelineState


class Second(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("second")
        context.set_metadata("order", order)


class First(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("first")
        context.set_metadata("order", order)


class Final(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("final")
        context.set_metadata("order", order)
        context.set_response(order)


async def _run_pipeline():
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(Second({}), PipelineStage.DELIVER)
    await plugins.register_plugin_for_stage(First({}), PipelineStage.DELIVER)
    await plugins.register_plugin_for_stage(Final({}), PipelineStage.DELIVER)

    caps = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="123",
    )
    await execute_pipeline("hi", caps, state=state)
    return state.response


def test_execute_pipeline_respects_registration_order():
    result = asyncio.run(_run_pipeline())
    assert result == ["second", "first", "final"]
