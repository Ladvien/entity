import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

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
    def __init__(self, results: list[str] | None = None) -> None:
        super().__init__({})
        self.results = results or []
        self.queries: list[str] = []
        self.added: list[str] = []

    async def add_embedding(self, text: str) -> None:
        self.added.append(text)

    async def query_similar(self, query: str, k: int = 5):
        self.queries.append(query)
        candidates = self.results + self.added
        return [t for t in candidates if query in t][:k]


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


@pytest.mark.asyncio
async def test_batch_store(simple_memory: Memory) -> None:
    pairs = {"k1": "v1", "k2": "v2"}
    await simple_memory.batch_store(pairs, user_id="default")
    for key, value in pairs.items():
        assert await simple_memory.get(key, user_id="default") == value


@pytest.mark.asyncio
async def test_vector_search(vector_memory: Memory) -> None:
    results = await vector_memory.vector_search("hello", k=1)
    assert results == ["hello world"]
    assert vector_memory.vector_store.queries == ["hello"]


@pytest.mark.asyncio
async def test_add_embedding(vector_memory: Memory) -> None:
    await vector_memory.add_embedding("foo")
    assert "foo" in vector_memory.vector_store.added


@pytest.mark.asyncio
async def test_conversation_search_vector(vector_memory: Memory) -> None:
    await vector_memory.add_conversation_entry(
        "conv",
        ConversationEntry(content="hello world", role="user", timestamp=datetime.now()),
        user_id="user1",
    )
    results = await vector_memory.conversation_search("hello", user_id="user1")
    assert len(results) == 1
    assert results[0]["content"] == "hello world"


@pytest.mark.asyncio
async def test_conversation_statistics(vector_memory: Memory) -> None:
    now = datetime.now()
    await vector_memory.add_conversation_entry(
        "c1",
        ConversationEntry(content="hi", role="user", timestamp=now),
        user_id="user1",
    )
    await vector_memory.add_conversation_entry(
        "c1",
        ConversationEntry(
            content="bye", role="assistant", timestamp=now + timedelta(seconds=30)
        ),
        user_id="user1",
    )
    await vector_memory.add_conversation_entry(
        "c2",
        ConversationEntry(
            content="ping", role="user", timestamp=now + timedelta(seconds=60)
        ),
        user_id="user1",
    )
    stats = await vector_memory.conversation_statistics("user1")
    assert stats["conversations"] == 2
    assert stats["messages"] == 3
    expected_avg = (len("hi") + len("bye") + len("ping")) / 3
    assert stats["average_length"] == expected_avg
    assert stats["last_activity"] == (now + timedelta(seconds=60)).isoformat()
