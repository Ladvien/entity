import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest

from entity_config.environment import load_env
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
from pipeline.resources.llm import UnifiedLLMResource
from pipeline.resources.memory import Memory
from plugins.builtin.resources.pg_vector_store import PgVectorStore
from plugins.builtin.resources.postgres import PostgresResource
from user_plugins.prompts.complex_prompt import ComplexPrompt

if hasattr(os, "geteuid") and os.geteuid() == 0:
    pytest.skip(
        "PostgreSQL integration test cannot run as root", allow_module_level=True
    )

load_env(Path(__file__).resolve().parents[2] / ".env")


@pytest.mark.integration
def test_vector_memory_integration(pg_env):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("PostgreSQL integration test cannot run as root")

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
        db = PostgresResource(db_cfg)
        vm = PgVectorStore(vm_cfg)
        vm.database = db
        memory = MemoryResource({})
        memory.database = db
        memory.vector_store = vm
        llm = UnifiedLLMResource(
            {"provider": "echo", "base_url": "http://localhost", "model": "none"}
        )
        try:
            await db.initialize()
            await vm.initialize()
        except Exception as exc:
            pytest.skip(f"PostgreSQL not available: {exc}")
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {db_cfg['history_table']}")
            await conn.execute(
                f"CREATE TABLE {db_cfg['history_table']} ("
                "conversation_id text, role text, content text, "
                "metadata jsonb, timestamp timestamptz)"
            )
        async with vm._db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {vm_cfg['table']}")
            await conn.execute(
                f"CREATE TABLE {vm_cfg['table']} "
                f"(text text, embedding vector({vm_cfg['dimensions']}))"
            )
        history_entry = ConversationEntry(
            content="previous", role="user", timestamp=datetime.now()
        )
        await memory.save_conversation("conv1", [history_entry])
        await vm.add_embedding("previous")
        resources = ResourceContainer()
        await resources.add("memory", memory)
        await resources.add("llm", llm)
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
        await db._pool.close()
        await vm._db._pool.close()
        return response

    result = asyncio.run(run())
    assert "Similar topics: previous" in result
