import pytest
from pipeline import PipelineStage, PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.context import PluginContext
from pipeline.errors import PluginContextError
from entity.core.state import PipelineState

from entity.core.resources.container import ResourceContainer


def test_set_response_disallowed_outside_deliver():
    state = PipelineState(conversation=[], pipeline_id="id")
    ctx = PluginContext(
        state, SystemRegistries(ResourceContainer(), ToolRegistry(), PluginRegistry())
    )
    ctx.set_current_stage(PipelineStage.PARSE)
    with pytest.raises(
        PluginContextError,
        match="set_response may only be called in DELIVER stage",
    ):
        ctx.set_response("nope")
    assert state.response is None
