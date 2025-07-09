import asyncio
from datetime import datetime

from pipeline import (ConversationEntry, MetricsCollector, PipelineState,
                      PluginContext, PluginRegistry, SystemRegistries,
                      ToolRegistry)
from pipeline.resources import ResourceContainer
from pipeline.resources.memory_resource import MemoryResource
from pipeline.stages import PipelineStage
from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource
from user_plugins.prompts.conversation_history import ConversationHistory


async def make_context(tmp_path):
    db = DuckDBDatabaseResource(
        {"path": tmp_path / "hist.duckdb", "history_table": "h"}
    )
    await db.initialize()
    memory = MemoryResource({})
    memory.database = db
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceContainer()
    await resources.add("memory", memory)
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    ctx = PluginContext(state, registries)
    return state, ctx, memory


def test_history_plugin_saves_conversation(tmp_path):
    state, ctx, memory = asyncio.run(make_context(tmp_path))
    plugin = ConversationHistory({"history_table": "h"})

    ctx.set_current_stage(PipelineStage.DELIVER)
    expected = ctx.get_conversation_history()
    asyncio.run(plugin.execute(ctx))

    saved = asyncio.run(
        memory.database.load_history(state.pipeline_id)  # type: ignore[attr-defined]
    )
    assert saved and saved[0].content == expected[0].content
