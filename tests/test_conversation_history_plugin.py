import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
from pipeline.resources.memory_resource import MemoryResource
from pipeline.stages import PipelineStage
from user_plugins.prompts.conversation_history import ConversationHistory


class FakeMemory(MemoryResource):
    def __init__(self) -> None:
        super().__init__(None, None, {})
        self.fetch = AsyncMock(return_value=[])
        self.execute = AsyncMock()
        self.history: list[ConversationEntry] = []

    async def load_conversation(self, conversation_id: str):
        return self.history

    async def save_conversation(self, conversation_id: str, history):
        self.history = history


def make_context(db: FakeMemory):
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", db))
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_history_plugin_saves_conversation():
    db = FakeMemory()
    state, ctx = make_context(db)
    plugin = ConversationHistory({"history_table": "tbl"})

    ctx.set_current_stage(PipelineStage.DELIVER)
    expected_history = ctx.get_conversation_history()
    asyncio.run(plugin.execute(ctx))

    assert db.history == expected_history
