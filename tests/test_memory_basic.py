import sqlite3
from contextlib import asynccontextmanager

import pytest
from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource


class SqliteDB(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memory_kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS conversation_history (conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)"
        )

    @asynccontextmanager
    async def connection(self):
        yield self.conn

    def get_connection_pool(self):
        return self.conn


@pytest.fixture()
async def simple_memory() -> Memory:
    mem = Memory(config={})
    mem.database = SqliteDB()
    mem.vector_store = None
    await mem.initialize()
    yield mem


@pytest.mark.asyncio
async def test_set_get(simple_memory: Memory) -> None:
    await simple_memory.set("foo", "bar", user_id="default")
    assert await simple_memory.get("foo", user_id="default") == "bar"


@pytest.mark.asyncio
async def test_remember_alias(simple_memory: Memory) -> None:
    assert Memory.remember is Memory.store_persistent
    await simple_memory.remember("alpha", 123, user_id="default")
    assert await simple_memory.get("alpha", user_id="default") == 123
