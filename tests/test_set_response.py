import asyncio
import pytest
from pipeline import PipelineStage, PipelineState, PluginContext, PromptPlugin
from registry import PluginRegistry, SystemRegistries, ToolRegistry

from entity.core.resources.container import ResourceContainer


def make_context(stage: PipelineStage) -> PluginContext:
    state = PipelineState(conversation=[], pipeline_id="1", current_stage=stage)
    capabilities = SystemRegistries(
        ResourceContainer(), ToolRegistry(), PluginRegistry()
    )
    return PluginContext(state, capabilities)


def test_set_response_allowed_in_deliver():
    ctx = make_context(PipelineStage.DELIVER)
    ctx.set_response("ok")
    assert ctx.response == "ok"


def test_set_response_fails_in_other_stage():
    ctx = make_context(PipelineStage.DO)
    with pytest.raises(
        ValueError, match="Only DELIVER stage plugins may set responses"
    ):
        ctx.set_response("nope")


class EarlyPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context: PluginContext) -> None:
        context.set_response("bad")


def test_plugin_cannot_set_response_before_deliver():
    ctx = make_context(PipelineStage.DO)
    plugin = EarlyPlugin({})
    with pytest.raises(ValueError):
        asyncio.run(plugin.execute(ctx))
