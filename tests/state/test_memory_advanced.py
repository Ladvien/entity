import pytest

from tests.conftest import AsyncPGDatabase
from entity.resources import Memory
from entity.resources.interfaces.vector_store import VectorStoreResource


class DummyVector(VectorStoreResource):
    def __init__(self) -> None:
        super().__init__({})
        self.entries: list[str] = []

    async def add_embedding(self, text: str) -> None:
        self.entries.append(text)

    async def query_similar(self, query: str, k: int = 5):
        return [t for t in self.entries if query in t][:k]


@pytest.fixture()
async def memory(postgres_dsn: str) -> Memory:
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = DummyVector()
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


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
