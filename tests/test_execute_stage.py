import asyncio
from datetime import datetime

import pytest

from entity.core.resources.container import ResourceContainer
from pipeline import (
    ConversationEntry,
    PipelineStage,
    PipelineState,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.pipeline import execute_stage


class GenericFailPlugin:
    stages = [PipelineStage.DO]

    async def execute(self, context):
        raise RuntimeError("boom", "extra")


class PropagatePlugin:
    stages = [PipelineStage.DO]

    async def execute(self, context):
        raise KeyError("oops")


def make_state():
    return PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="123",
    )


def make_capabilities(plugin):
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(plugin, PipelineStage.DO))
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_generic_error_sets_failure_info():
    state = make_state()
    capabilities = make_capabilities(GenericFailPlugin())
    asyncio.run(execute_stage(PipelineStage.DO, state, capabilities))
    assert state.failure_info is not None
    assert state.failure_info.error_message == "boom"


def test_unexpected_error_propagates():
    state = make_state()
    capabilities = make_capabilities(PropagatePlugin())
    with pytest.raises(KeyError):
        asyncio.run(execute_stage(PipelineStage.DO, state, capabilities))
    assert state.failure_info is not None
    assert state.failure_info.error_message == "oops"
