import types
import asyncio
import json
from datetime import datetime
import duckdb
from contextlib import asynccontextmanager

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from entity.core.context import PluginContext
from entity.core.state import PipelineState, ConversationEntry
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


class DummyConnection:
    def __init__(self, store: dict) -> None:
        self.store = store

    async def execute(self, query: str, params: tuple) -> None:
        if query.startswith("DELETE FROM conversation_history"):
            cid = params[0] if isinstance(params, tuple) else params
            self.store.setdefault("history", {}).pop(cid, None)
        elif query.startswith("INSERT INTO conversation_history"):
            cid, role, content, metadata, ts = params
            self.store.setdefault("history", {}).setdefault(cid, []).append(
                (role, content, json.loads(metadata), ts)
            )
        elif query.startswith("DELETE FROM kv_store"):
            key = params[0] if isinstance(params, tuple) else params
            self.store.setdefault("kv", {}).pop(key, None)
        elif query.startswith("INSERT INTO kv_store"):
            key, value = params
            self.store.setdefault("kv", {})[key] = json.loads(value)

    async def fetch(self, query: str, params: tuple) -> list:
        if query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            cid = params[0] if isinstance(params, tuple) else params
            return [
                (role, content, metadata, ts)
                for role, content, metadata, ts in self.store.get("history", {}).get(
                    cid, []
                )
            ]
        if query.startswith("SELECT value FROM kv_store"):
            key = params[0] if isinstance(params, tuple) else params
            if key in self.store.get("kv", {}):
                return [(json.dumps(self.store["kv"][key]),)]
        return []


class DummyDatabase(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})
        self.data: dict = {"history": {}, "kv": {}}

    @asynccontextmanager
    async def connection(self):
        yield DummyConnection(self.data)


class DummyPool(DummyDatabase):
    pass


class DummyRegistries:
    def __init__(self, path: str) -> None:
        db = DuckDBResource(path)
        mem = Memory(config={})
        mem.database = db
        mem.vector_store = None
        asyncio.get_event_loop().run_until_complete(mem.initialize())
        self.resources = {"memory": mem}
        self.tools = types.SimpleNamespace()


def make_context(tmp_path) -> PluginContext:
    state = PipelineState(conversation=[])
    regs = DummyRegistries(str(tmp_path / "mem.duckdb"))
    return PluginContext(state, regs)


def test_memory_roundtrip(tmp_path) -> None:
    ctx = make_context(tmp_path)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ctx.remember("foo", "bar"))
    assert loop.run_until_complete(ctx.memory("foo")) == "bar"


def test_memory_persists_between_instances() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    db = DummyDatabase()
    mem1 = Memory(config={})
    mem1.database = db
    mem1.vector_store = None
    asyncio.get_event_loop().run_until_complete(mem1.initialize())
    mem1.set("foo", "bar")
    entry = ConversationEntry("hi", "user", datetime.now())
    loop.run_until_complete(mem1.save_conversation("cid", [entry]))

    mem2 = Memory(config={})
    mem2.database = db
    mem2.vector_store = None
    asyncio.get_event_loop().run_until_complete(mem2.initialize())
    assert mem2.get("foo") == "bar"
    history = loop.run_until_complete(mem2.load_conversation("cid"))
    assert history == [entry]


def test_memory_persists_with_connection_pool() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    pool = DummyPool()
    mem1 = Memory(config={})
    mem1.database = pool
    mem1.vector_store = None
    asyncio.get_event_loop().run_until_complete(mem1.initialize())
    mem1.set("foo", "bar")
    entry = ConversationEntry("hi", "user", datetime.now())
    loop.run_until_complete(mem1.save_conversation("cid", [entry]))

    mem2 = Memory(config={})
    mem2.database = pool
    mem2.vector_store = None
    asyncio.get_event_loop().run_until_complete(mem2.initialize())
    assert mem2.get("foo") == "bar"
    history = loop.run_until_complete(mem2.load_conversation("cid"))
    assert history == [entry]


def test_initialize_without_database_raises_error() -> None:
    mem = Memory(config={})
    with pytest.raises(ResourceInitializationError):
        asyncio.run(mem.initialize())
