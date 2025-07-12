import types
import pytest

from contextlib import asynccontextmanager
from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory
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
            self.db.history.pop(params[0], None)
            return []
        if query.startswith("INSERT INTO conversation_history"):
            cid, role, content, metadata, ts = params
            self.db.history.setdefault(cid, []).append((role, content, metadata, ts))
            return []
        if query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            return self.db.history.get(params[0], [])
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


class DummyVector(VectorStoreResource):
    def __init__(self) -> None:
        super().__init__({})

    async def add_embedding(self, text: str) -> None:
        return None

    async def query_similar(self, query: str, k: int = 5) -> list[str]:
        return []


class DummyRegistries:
    def __init__(self, memory) -> None:
        self.resources = {"memory": memory}
        self.tools = types.SimpleNamespace()


def make_context(memory) -> PluginContext:
    state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries(memory))


@pytest.mark.asyncio
async def test_memory_roundtrip(memory_db) -> None:
    ctx = make_context(memory_db)
    ctx.remember("foo", "bar")

    assert ctx.memory("foo") == "bar"
    ctx2 = make_context(memory_db)
    assert ctx2.memory("foo") == "bar"
