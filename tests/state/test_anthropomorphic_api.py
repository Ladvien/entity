import types

import pytest

from tests.conftest import AsyncPGDatabase
from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory


class DummyRegistries:
    def __init__(self, mem: Memory) -> None:
        self.resources = {"memory": mem}
        self.tools = types.SimpleNamespace()


@pytest.fixture()
async def context(postgres_dsn: str) -> PluginContext:
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    regs = DummyRegistries(mem)
    try:
        yield PluginContext(PipelineState(conversation=[]), regs)
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


@pytest.mark.asyncio
async def test_remember_recall_interop(context: PluginContext) -> None:
    await context.remember("foo", "bar")
    assert await context._memory.fetch_persistent("foo", user_id="default") == "bar"
    await context._memory.store_persistent("baz", 123, user_id="default")
    assert await context.recall("baz") == 123


@pytest.mark.asyncio
async def test_think_reflect_roundtrip(context: PluginContext) -> None:
    await context.think("idea", 42)
    assert await context.reflect("idea") == 42
