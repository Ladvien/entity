import types
import pytest

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from contextlib import asynccontextmanager
from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory
from entity.resources import memory as memory_module
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.interfaces.vector_store import VectorStoreResource


class _DBConn:
    def __init__(self, db: "DummyDB") -> None:
        self.db = db

    async def execute(self, query: str, params: tuple) -> list:
        if query.startswith("DELETE FROM memory_kv"):
            if "WHERE" in query:
                self.db.kv.pop(params[0], None)
            else:
                self.db.kv.clear()
            return []
        if query.startswith("INSERT INTO memory_kv"):
            self.db.kv[params[0]] = params[1]
            return []
        if query.startswith("SELECT value FROM memory_kv"):
            return [(self.db.kv.get(params[0]),)]
        if query.startswith("DELETE FROM conversation_history"):
            cid = params[0] if isinstance(params, tuple) else params
            self.store["history"].pop(cid, None)
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

    async def fetch(self, query: str, params: tuple) -> list:
        return await self.execute(query, params)


class DummyDB(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})
        self.kv: dict[str, str] = {}
        self.history: dict[str, list] = {}

    @asynccontextmanager
    async def connection(self):
        yield _DBConn(self)


class DummyPool(DummyDatabase):
    pass


class DummyRegistries:
    def __init__(self) -> None:
        db = DummyDatabase()
        memory_module.database = db
        memory_module.vector_store = None
        memory = Memory(config={})
        self.resources = {"memory": memory}
        self.tools = types.SimpleNamespace()


def make_context(memory) -> PluginContext:
    state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries(memory))


def test_memory_roundtrip() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    ctx = make_context()
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
