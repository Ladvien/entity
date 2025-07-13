import sqlite3
from contextlib import asynccontextmanager
import pytest

from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.interfaces.vector_store import VectorStoreResource


class InMemoryDB(DatabaseResource):
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
    def __init__(self) -> None:
        super().__init__({})
        self.entries: list[str] = []

    async def add_embedding(self, text: str) -> None:
        self.entries.append(text)

    async def query_similar(self, query: str, k: int = 5):
        return [t for t in self.entries if query in t][:k]


@pytest.fixture()
async def memory() -> Memory:
    mem = Memory(config={})
    mem.database = InMemoryDB()
    mem.vector_store = DummyVector()
    await mem.initialize()
    yield mem


@pytest.mark.asyncio
async def test_sql_query(memory: Memory) -> None:
    await memory.set("foo", "bar")
    rows = await memory.query(
        "SELECT value FROM memory_kv WHERE key = ?",
        ["default:foo"],
    )
    assert rows and rows[0]["value"] == '"bar"'


@pytest.mark.asyncio
async def test_vector_search(memory: Memory) -> None:
    await memory.add_embedding("hello there")
    result = await memory.vector_search("hello")
    assert result == ["hello there"]
