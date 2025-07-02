import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest

from config.environment import load_env
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
from pipeline.plugins.prompts.complex_prompt import ComplexPrompt
from pipeline.plugins.resources.echo_llm import EchoLLMResource
from pipeline.plugins.resources.pg_vector_store import PgVectorStore
from pipeline.plugins.resources.postgres_database import PostgresDatabaseResource

load_env(Path(__file__).resolve().parents[2] / ".env")


@pytest.mark.integration
def test_vector_memory_integration():
    async def run():
        db_cfg = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": 5432,
            "name": os.environ.get("DB_NAME", os.environ.get("DB_USER", "dev_db")),
            "username": os.environ.get(
                "DB_USER", os.environ.get("DB_USERNAME", "agent")
            ),
            "password": os.environ.get("DB_PASSWORD", ""),
            "history_table": "test_history_int",
        }
        vm_cfg = {
            "host": db_cfg["host"],
            "port": db_cfg["port"],
            "name": db_cfg["name"],
            "username": db_cfg["username"],
            "password": db_cfg["password"],
            "table": "test_vectors_int",
            "dimensions": 3,
        }
        db = PostgresDatabaseResource(db_cfg)
        vm = PgVectorStore(vm_cfg)
        llm = EchoLLMResource()
        try:
            await db.initialize()
            await vm.initialize()
        except OSError as exc:
            pytest.skip(f"PostgreSQL not available: {exc}")
        await db._connection.execute(f"DROP TABLE IF EXISTS {db_cfg['history_table']}")
        await db._connection.execute(
            f"CREATE TABLE {db_cfg['history_table']} ("
            "conversation_id text, role text, content text, "
            "metadata jsonb, timestamp timestamptz)"
        )
        await vm._connection.execute(f"DROP TABLE IF EXISTS {vm_cfg['table']}")
        await vm._connection.execute(
            f"CREATE TABLE {vm_cfg['table']} (text text, embedding vector({vm_cfg['dimensions']}))"
        )
        history_entry = ConversationEntry(
            content="previous", role="user", timestamp=datetime.now()
        )
        await db.save_history("conv1", [history_entry])
        await vm.add_embedding("previous")
        resources = ResourceRegistry()
        resources.add("database", db)
        resources.add("vector_memory", vm)
        resources.add("llm", llm)
        registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
        state = PipelineState(
            conversation=[
                ConversationEntry(
                    content="previous", role="user", timestamp=datetime.now()
                )
            ],
            pipeline_id="conv1",
            metrics=MetricsCollector(),
        )
        ctx = PluginContext(state, registries)
        plugin = ComplexPrompt({"k": 1})
        await plugin.execute(ctx)
        response = state.response
        await db._connection.close()
        await vm._connection.close()
        return response

    result = asyncio.run(run())
    assert "Similar topics: previous" in result
