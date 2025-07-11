import asyncio
from datetime import datetime

import pytest

from entity.core.state import ConversationEntry
from entity.resources.memory import Memory
from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource


@pytest.mark.integration
def test_memory_persists_through_database(tmp_path):
    async def run():
        db = DuckDBDatabaseResource({"path": str(tmp_path / "mem.db")})
        memory = Memory()
        memory.database = db
        await db.initialize()
        async with db.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS conversation_history ("
                "conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)"
            )
        entries = [
            ConversationEntry(content="hello", role="user", timestamp=datetime.now())
        ]
        await memory.save_conversation("conv1", entries)
        memory._conversations.clear()
        loaded = await memory.load_conversation("conv1")
        await db.shutdown()
        return loaded

    history = asyncio.run(run())
    assert len(history) == 1
    assert history[0].content == "hello"
