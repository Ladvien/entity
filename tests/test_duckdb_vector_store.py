import asyncio

from plugins.resources.duckdb_vector_store import DuckDBVectorStore


def test_vector_store_roundtrip(tmp_path):
    async def run():
        cfg = {"path": tmp_path / "vec.duckdb", "table": "vectors", "dimensions": 3}
        store = DuckDBVectorStore(cfg)
        await store.initialize()
        await store.add_embedding("hello")
        results = await store.query_similar("hello", 1)
        await store.shutdown()
        return results

    result = asyncio.run(run())
    assert result == ["hello"]
