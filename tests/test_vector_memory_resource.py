import asyncio

from plugins.builtin.resources.duckdb_vector_store import DuckDBVectorStore


async def store_roundtrip(tmp_path) -> list[str]:
    cfg = {"path": tmp_path / "vec.duckdb", "table": "vectors", "dimensions": 3}
    store = DuckDBVectorStore(cfg)
    await store.initialize()
    await store.add_embedding("hello")
    result = await store.query_similar("hello", 1)
    await store.shutdown()
    return result


def test_store_roundtrip(tmp_path):
    result = asyncio.run(store_roundtrip(tmp_path))
    assert result == ["hello"]
