from __future__ import annotations

import asyncio
from datetime import datetime

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
    )
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(DummyPlugin(), PipelineStage.DO))
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    called = False

    def validate(ctx):
        nonlocal called
        called = True
        assert ctx.current_stage == PipelineStage.DO

    capabilities.validators.register(PipelineStage.DO, validate)
    asyncio.run(execute_stage(PipelineStage.DO, state, capabilities))
    assert called
    assert any(e.content == "done" for e in state.conversation)
