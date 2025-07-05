import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest
from plugins.builtin.resources.postgres import PostgresResource

from config.environment import load_env
from pipeline.resources.memory_resource import MemoryResource
from pipeline.state import ConversationEntry

load_env(Path(__file__).resolve().parents[2] / ".env")

CONN = {
    "host": os.environ["DB_HOST"],
    "port": 5432,
    "name": os.environ["DB_NAME"],
    "username": os.environ["DB_USERNAME"],
    "password": os.environ.get("DB_PASSWORD", ""),
    "pool_min_size": 1,
    "pool_max_size": 2,
    "history_table": "test_history",
}


@pytest.mark.integration
def test_save_and_load_history():
    async def run():
        db = PostgresResource(CONN)
        memory = MemoryResource(database=db)
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
