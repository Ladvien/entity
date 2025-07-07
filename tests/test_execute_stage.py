import asyncio
from datetime import datetime

import pytest

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineStage,
    PipelineState,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.pipeline import execute_stage
from pipeline.resources import ResourceContainer


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
        metrics=MetricsCollector(),
    )


def make_registries(plugin):
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(plugin, PipelineStage.DO)
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_generic_error_sets_failure_info():
    state = make_state()
    registries = make_registries(GenericFailPlugin())
    asyncio.run(execute_stage(PipelineStage.DO, state, registries))
    assert state.failure_info is not None
    assert state.failure_info.error_message == "boom"


def test_unexpected_error_propagates():
    state = make_state()
    registries = make_registries(PropagatePlugin())
    with pytest.raises(KeyError):
        asyncio.run(execute_stage(PipelineStage.DO, state, registries))
    assert state.failure_info is not None
    assert state.failure_info.error_message == "oops"
