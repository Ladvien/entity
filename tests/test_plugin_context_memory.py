import types
from datetime import datetime
import asyncio
import json

from contextlib import asynccontextmanager

from entity.core.context import PluginContext
from entity.core.state import ConversationEntry, PipelineState
from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource


class DummyConnection:
    def __init__(self, store: dict) -> None:
        self.store = store

    async def execute(self, query: str, params: tuple) -> None:
        if query.startswith("DELETE FROM conversation_history"):
            cid = params
            self.store["history"].pop(cid, None)
        elif query.startswith("INSERT INTO conversation_history"):
            cid, role, content, metadata, ts = params
            self.store.setdefault("history", {}).setdefault(cid, []).append(
                (role, content, json.loads(metadata), ts)
            )
        elif query.startswith("DELETE FROM kv_store"):
            key = params
            self.store.setdefault("kv", {}).pop(key, None)
        elif query.startswith("INSERT INTO kv_store"):
            key, value = params
            self.store.setdefault("kv", {})[key] = json.loads(value)

    async def fetch(self, query: str, params: tuple) -> list:
        if query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            cid = params
            return [
                (role, content, metadata, ts)
                for role, content, metadata, ts in self.store.get("history", {}).get(
                    cid, []
                )
            ]
        if query.startswith("SELECT value FROM kv_store"):
            key = params
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


class DummyRegistries:
    def __init__(self) -> None:
        db = DummyDatabase()
        self.resources = {"memory": Memory(database=db, config={})}
        self.tools = types.SimpleNamespace()


def make_context() -> PluginContext:
    state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries())


def test_memory_roundtrip() -> None:
    ctx = make_context()
    ctx.remember("foo", "bar")

    assert ctx.memory("foo") == "bar"


def test_memory_persists_between_instances() -> None:
    db = DummyDatabase()
    mem1 = Memory(database=db, config={})
    mem1.set("foo", "bar")
    entry = ConversationEntry("hi", "user", datetime.now())
    asyncio.run(mem1.save_conversation("cid", [entry]))

    mem2 = Memory(database=db, config={})
    assert mem2.get("foo") == "bar"
    history = asyncio.run(mem2.load_conversation("cid"))
    assert history == [entry]
