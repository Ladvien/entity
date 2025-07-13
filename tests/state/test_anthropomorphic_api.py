import sqlite3
from contextlib import asynccontextmanager
import types
import pytest

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource


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


class DummyRegistries:
    def __init__(self, mem: Memory) -> None:
        self.resources = {"memory": mem}
        self.tools = types.SimpleNamespace()


@pytest.fixture()
async def context() -> PluginContext:
    mem = Memory(config={})
    mem.database = InMemoryDB()
    mem.vector_store = None
    await mem.initialize()
    regs = DummyRegistries(mem)
    return PluginContext(PipelineState(conversation=[]), regs)


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
