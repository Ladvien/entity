import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest

from entity_config.environment import load_env
from pipeline.resources.memory import Memory
from pipeline.state import ConversationEntry
from plugins.builtin.resources.postgres import PostgresResource

load_env(Path(__file__).resolve().parents[2] / ".env")

CONN = {
    "host": os.environ.get("DB_HOST", ""),
    "port": 5432,
    "name": os.environ.get("DB_NAME", ""),
    "username": os.environ.get("DB_USERNAME", ""),
    "password": os.environ.get("DB_PASSWORD", ""),
    "pool_min_size": 1,
    "pool_max_size": 2,
    "history_table": "test_history",
}


@pytest.mark.integration
def test_save_and_load_history(pg_env):
    async def run():
        db = PostgresResource(CONN)
        memory = MemoryResource({})
        memory.database = db
        try:
            await db.initialize()
        except OSError as exc:
            pytest.skip(f"PostgreSQL not available: {exc}")
        async with db.connection() as conn:
            await conn.execute("DROP TABLE IF EXISTS test_history")
            await conn.execute(
                "CREATE TABLE test_history ("
                "conversation_id text, role text, content text, "
                "metadata jsonb, timestamp timestamptz)"
            )
        entries = [
            ConversationEntry(content="hello", role="user", timestamp=datetime.now())
        ]
        await memory.save_conversation("conv1", entries)
        loaded = await memory.load_conversation("conv1")
        await db._pool.close()
        return loaded

    history = asyncio.run(run())
    assert len(history) == 1
    assert history[0].content == "hello"
