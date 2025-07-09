import pytest

from pipeline import PipelineStage, PipelineState, PluginContext
from registry import PluginRegistry, SystemRegistries, ToolRegistry
from pipeline.resources import ResourceContainer


def make_context(stage: PipelineStage) -> PluginContext:
    state = PipelineState(conversation=[], pipeline_id="1", current_stage=stage)
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), PluginRegistry())
    return PluginContext(state, registries)


def test_set_response_allowed_in_deliver():
    ctx = make_context(PipelineStage.DELIVER)
    ctx.set_response("ok")
    assert ctx.response == "ok"


def test_set_response_fails_in_other_stage():
    ctx = make_context(PipelineStage.DO)
    with pytest.raises(ValueError):
        ctx.set_response("nope")
