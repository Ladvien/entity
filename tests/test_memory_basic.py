import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime

import pytest
from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.interfaces.vector_store import VectorStoreResource
from entity.core.state import ConversationEntry


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


class DummyVector(VectorStoreResource):
    def __init__(self, results: list[str]) -> None:
        super().__init__({})
        self.results = results
        self.queries: list[str] = []

    async def add_embedding(self, text: str) -> None:
        return None

    async def query_similar(self, query: str, k: int = 5):
        self.queries.append(query)
        return self.results[:k]


@pytest.fixture()
async def simple_memory() -> Memory:
    mem = Memory(config={})
    mem.database = SqliteDB()
    mem.vector_store = None
    await mem.initialize()
    yield mem


@pytest.fixture()
async def vector_memory() -> Memory:
    mem = Memory(config={})
    mem.database = SqliteDB()
    mem.vector_store = DummyVector(["hello world"])
    await mem.initialize()
    await mem.add_conversation_entry(
        "user1_conv1",
        ConversationEntry(
            content="hello world",
            role="user",
            timestamp=datetime.now(),
        ),
    )
    yield mem


@pytest.mark.asyncio
async def test_set_get(simple_memory: Memory) -> None:
    await simple_memory.set("foo", "bar")
    assert await simple_memory.get("foo") == "bar"


@pytest.mark.asyncio
async def test_remember_alias(simple_memory: Memory) -> None:
    assert Memory.remember is Memory.store_persistent
    await simple_memory.remember("alpha", 123)
    assert await simple_memory.get("alpha") == 123


@pytest.mark.asyncio
async def test_user_isolation(simple_memory: Memory) -> None:
    await simple_memory.store_persistent("foo", "a", user_id="u1")
    await simple_memory.store_persistent("foo", "b", user_id="u2")
    assert await simple_memory.fetch_persistent("foo", user_id="u1") == "a"
    assert await simple_memory.fetch_persistent("foo", user_id="u2") == "b"
    assert await simple_memory.fetch_persistent("foo", user_id="u3") is None
