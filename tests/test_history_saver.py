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
from pipeline.plugins.prompts.conversation_history_saver import ConversationHistorySaver


class FakeDB:
    name = "database"

    def __init__(self) -> None:
        self.save_history = AsyncMock()


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


def test_history_saver_invokes_db():
    db = FakeDB()
    state, ctx = make_context(db)
    plugin = ConversationHistorySaver({})

    expected_history = ctx.get_conversation_history()
    asyncio.run(plugin.execute(ctx))

    db.save_history.assert_awaited_with("1", expected_history)
