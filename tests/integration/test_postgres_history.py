import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest

from config.environment import load_env
from pipeline import (
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.plugins.prompts.conversation_history import ConversationHistory
from pipeline.plugins.resources.postgres import PostgresResource
from pipeline.state import ConversationEntry, PipelineStage

load_env(Path(__file__).resolve().parents[2] / ".env")

CONN = {
    "host": os.environ["DB_HOST"],
    "port": 5432,
    "name": os.environ["DB_NAME"],
    "username": os.environ["DB_USERNAME"],
    "password": os.environ.get("DB_PASSWORD", ""),
    "history_table": "test_history",
}


@pytest.mark.integration
def test_save_and_load_history():
    async def run():
        db = PostgresResource(CONN)
        plugin = ConversationHistory(CONN)
        try:
            await db.initialize()
        except OSError as exc:
            pytest.skip(f"PostgreSQL not available: {exc}")
<<<<<<< HEAD
        await db.execute("DROP TABLE IF EXISTS test_history")
        await db.execute(
=======
        await resource._pool.execute("DROP TABLE IF EXISTS test_history")
        await resource._pool.execute(
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc
            "CREATE TABLE test_history ("
            ""
            "conversation_id text, role text, content text, "
            "metadata jsonb, timestamp timestamptz)"
        )
<<<<<<< HEAD
        state = PipelineState(
            conversation=[], pipeline_id="conv1", metrics=MetricsCollector()
        )
        resources = ResourceRegistry()
        resources.add("database", db)
        registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
        ctx = PluginContext(state, registries)
        ctx._state.current_stage = PipelineStage.PARSE
        await plugin.execute(ctx)
        entry = ConversationEntry(
            content="hello", role="user", timestamp=datetime.now()
        )
        ctx.add_conversation_entry(
            content=entry.content, role=entry.role, timestamp=entry.timestamp
        )
        ctx._state.current_stage = PipelineStage.DELIVER
        await plugin.execute(ctx)
        rows = await db.fetch(
            "SELECT content FROM test_history WHERE conversation_id=$1", "conv1"
        )
        await db.execute("DROP TABLE IF EXISTS test_history")
        return rows
=======
        entries = [
            ConversationEntry(content="hello", role="user", timestamp=datetime.now())
        ]
        await resource.save_history("conv1", entries)
        loaded = await resource.load_history("conv1")
        await resource.shutdown()
        return loaded
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc

    result = asyncio.run(run())
    assert len(result) == 1
