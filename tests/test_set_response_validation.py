import asyncio
import pytest

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.context import PluginContext
from pipeline.state import PipelineState
from pipeline.resources import ResourceContainer


def test_set_response_disallowed_outside_deliver():
    state = PipelineState(conversation=[], pipeline_id="id")
    ctx = PluginContext(
        state, SystemRegistries(ResourceContainer(), ToolRegistry(), PluginRegistry())
    )
    ctx.set_current_stage(PipelineStage.PARSE)
    with pytest.raises(ValueError):
        ctx.set_response("nope")
    assert state.response is None
