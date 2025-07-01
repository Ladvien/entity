import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.plugins.prompts.conversation_history import ConversationHistory
from pipeline.stages import PipelineStage


class FakeDB:
    name = "database"

    def __init__(self) -> None:
        self.fetch = AsyncMock(return_value=[])
        self.execute = AsyncMock()
        self.history: list[tuple] = []


def make_context(db: FakeDB):
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceRegistry()
    resources.add("database", db)
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_history_plugin_saves_conversation():
    db = FakeDB()
    state, ctx = make_context(db)
    plugin = ConversationHistory({"history_table": "tbl"})

    ctx._state.current_stage = PipelineStage.DELIVER
    expected_history = ctx.get_conversation_history()
    asyncio.run(plugin.execute(ctx))

    assert db.execute.await_count == len(expected_history)
