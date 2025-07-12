import types
import asyncio
import duckdb
from contextlib import asynccontextmanager

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
from pipeline.errors import ResourceInitializationError
import pytest


class DuckDBResource(DatabaseResource):
    def __init__(self, path: str) -> None:
        super().__init__({})
        self.conn = duckdb.connect(path)
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
    def __init__(self, path: str) -> None:
        db = DuckDBResource(path)
        mem = Memory(config={})
        mem.database = db
        mem.vector_store = None
        self.resources = {"memory": mem}
        self.tools = types.SimpleNamespace()


def make_context(tmp_path) -> PluginContext:
    state = PipelineState(conversation=[])
    regs = DummyRegistries(str(tmp_path / "mem.duckdb"))
    return PluginContext(state, regs)


def test_memory_roundtrip(tmp_path) -> None:
    ctx = make_context(tmp_path)
    ctx.remember("foo", "bar")

    assert ctx.memory("foo") == "bar"


def test_memory_persists_between_instances() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    db = DummyDatabase()
    memory_module.database = db
    memory_module.vector_store = None
    mem1 = Memory(config={})
    mem1.set("foo", "bar")
    entry = ConversationEntry("hi", "user", datetime.now())
    loop.run_until_complete(mem1.save_conversation("cid", [entry]))

    mem2 = Memory(config={})
    assert mem2.get("foo") == "bar"
    history = loop.run_until_complete(mem2.load_conversation("cid"))
    assert history == [entry]


def test_memory_persists_with_connection_pool() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    pool = DummyPool()
    memory_module.database = pool
    memory_module.vector_store = None
    mem1 = Memory(config={})
    mem1.set("foo", "bar")
    entry = ConversationEntry("hi", "user", datetime.now())
    loop.run_until_complete(mem1.save_conversation("cid", [entry]))

    mem2 = Memory(config={})
    assert mem2.get("foo") == "bar"
    history = loop.run_until_complete(mem2.load_conversation("cid"))
    assert history == [entry]


def test_initialize_without_database_raises_error() -> None:
    mem = Memory(config={})
    with pytest.raises(ResourceInitializationError):
        asyncio.run(mem.initialize())
