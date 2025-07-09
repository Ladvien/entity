from __future__ import annotations

import asyncio
from datetime import datetime

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
from entity.core.resources.container import ResourceContainer


class DummyPlugin:
    stages = [PipelineStage.DO]

    async def execute(self, context):
        context.add_conversation_entry("done", "system")


def test_validator_runs_before_plugin():
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(DummyPlugin(), PipelineStage.DO))
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    called = False

    def validate(ctx):
        nonlocal called
        called = True
        assert ctx.current_stage == PipelineStage.DO

    registries.validators.register(PipelineStage.DO, validate)
    asyncio.run(execute_stage(PipelineStage.DO, state, registries))
    assert called
    assert any(e.content == "done" for e in state.conversation)
