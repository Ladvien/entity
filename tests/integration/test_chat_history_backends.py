import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest

from config.environment import load_env
from pipeline import (ConversationEntry, MetricsCollector, PipelineStage,
                      PipelineState, PluginContext, PluginRegistry,
                      ResourceRegistry, SystemRegistries, ToolRegistry)
from pipeline.plugins.prompts.chat_history import ChatHistory
<<<<<<< HEAD
from pipeline.plugins.resources.duckdb_database import DuckDBDatabaseResource
from pipeline.plugins.resources.in_memory_storage import \
    InMemoryStorageResource
from pipeline.plugins.resources.memory import MemoryResource
from pipeline.plugins.resources.postgres import PostgresResource
from pipeline.plugins.resources.sqlite_storage import SQLiteStorageResource
=======
from pipeline.resources.duckdb_database import DuckDBDatabaseResource
from pipeline.resources.in_memory_storage import InMemoryStorageResource
from pipeline.resources.memory_resource import MemoryResource
from pipeline.resources.postgres_database import PostgresDatabaseResource
from pipeline.resources.sqlite_storage import SQLiteStorageResource
>>>>>>> 31c26c6f08f011fda24b488de4c679ad0b2325fd

load_env(Path(__file__).resolve().parents[2] / ".env")


async def run_history_test(resource):
    await getattr(resource, "initialize", lambda: None)()
    if isinstance(resource, PostgresResource):
        async with resource.connection() as conn:
            await conn.execute("DROP TABLE IF EXISTS test_history")
            await conn.execute(
                "CREATE TABLE test_history ("
                "conversation_id text, role text, content text, "
                "metadata jsonb, timestamp timestamptz)"
            )
    if isinstance(resource, SQLiteStorageResource):
        resource._table = "test_history"
        await resource.initialize()
    if isinstance(resource, DuckDBDatabaseResource):
        resource._history_table = "test_history"
        await resource.initialize()

    memory = MemoryResource(resource)
    resources = ResourceRegistry()
    resources.add("memory", memory)
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="conv1",
        metrics=MetricsCollector(),
    )
    ctx = PluginContext(state, registries)
    ctx.set_current_stage(PipelineStage.DELIVER)
    plugin = ChatHistory({})
    await plugin.execute(ctx)

    new_state = PipelineState(
        conversation=[], pipeline_id="conv1", metrics=MetricsCollector()
    )
    new_ctx = PluginContext(new_state, registries)
    new_ctx.set_current_stage(PipelineStage.PARSE)
    await plugin.execute(new_ctx)
    await getattr(resource, "shutdown", lambda: None)()
    return new_ctx.get_conversation_history()


@pytest.mark.integration
def test_in_memory_history():
    history = asyncio.run(run_history_test(InMemoryStorageResource({})))
    assert history and history[0].content == "hi"


@pytest.mark.integration
def test_sqlite_history(tmp_path):
    history = asyncio.run(
        run_history_test(SQLiteStorageResource({"path": tmp_path / "db.sqlite3"}))
    )
    assert history and history[0].content == "hi"


@pytest.mark.integration
def test_duckdb_history(tmp_path):
    history = asyncio.run(
        run_history_test(
            DuckDBDatabaseResource(
                {"path": tmp_path / "db.duckdb", "history_table": "test_history"}
            )
        )
    )
    assert history and history[0].content == "hi"


@pytest.mark.integration
def test_postgres_history():
    cfg = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": 5432,
        "name": os.environ.get("DB_NAME", "dev_db"),
        "username": os.environ.get("DB_USERNAME", "agent"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "history_table": "test_history",
    }
    try:
        resource = PostgresResource(cfg)
        asyncio.run(resource.initialize())
    except OSError as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")
    history = asyncio.run(run_history_test(resource))
    assert history and history[0].content == "hi"
