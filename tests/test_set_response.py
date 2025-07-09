import pytest
from pipeline import PipelineStage, PipelineState, PluginContext
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry

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
