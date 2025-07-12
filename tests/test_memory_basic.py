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
async def test_conversation_search_sql_fallback(simple_memory: Memory) -> None:
    await simple_memory.add_conversation_entry(
        "user1_conv1",
        ConversationEntry(
            content="where is the meeting",
            role="user",
            timestamp=datetime.now(),
        ),
    )
    results = await simple_memory.conversation_search("meeting")
    assert len(results) == 1
    assert results[0]["content"] == "where is the meeting"


@pytest.mark.asyncio
async def test_conversation_search_vector(vector_memory: Memory) -> None:
    results = await vector_memory.conversation_search("hello")
    assert len(results) == 1
    assert results[0]["content"] == "hello world"
    vector = vector_memory.vector_store
    assert isinstance(vector, DummyVector)
    assert vector.queries == ["hello"]
