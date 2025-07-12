import asyncio
from datetime import datetime

import pytest
from entity.core.resources.container import ResourceContainer
from entity.core.state import ConversationEntry, PipelineState
from entity.core.context import PluginContext
from pipeline import PluginRegistry, SystemRegistries, ToolRegistry


def _make_context() -> PluginContext:
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
    )
    caps = SystemRegistries(ResourceContainer(), ToolRegistry(), PluginRegistry())
    return PluginContext(state, caps)


@pytest.mark.unit
def test_queue_tool_use_unknown_tool():
    ctx = _make_context()
    with pytest.raises(ValueError):
        asyncio.run(ctx.queue_tool_use("missing"))
