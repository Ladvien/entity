import asyncio
import pytest

from entity.plugins.context import PluginContext
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


@pytest.mark.asyncio
async def test_remember_isolated_by_user_id():
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx_a = PluginContext({}, user_id="a", memory=memory)
    ctx_b = PluginContext({}, user_id="b", memory=memory)

    await ctx_a.remember("val", 1)
    await ctx_b.remember("val", 2)

    assert await ctx_a.recall("val") == 1
    assert await ctx_b.recall("val") == 2


@pytest.mark.asyncio
async def test_memory_thread_safety_with_concurrent_users():
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx_a = PluginContext({}, user_id="a", memory=memory)
    ctx_b = PluginContext({}, user_id="b", memory=memory)

    await asyncio.gather(
        ctx_a.remember("count", 1),
        ctx_b.remember("count", 2),
    )
    results = await asyncio.gather(
        ctx_a.recall("count"),
        ctx_b.recall("count"),
    )
    assert results == [1, 2]
