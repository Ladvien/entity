import pytest

from entity.resources import Memory


@pytest.fixture()
async def memory(pg_vector_memory: Memory) -> Memory:
    yield pg_vector_memory


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
