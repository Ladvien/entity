import types
import asyncio
import json
from datetime import datetime
import duckdb
from contextlib import asynccontextmanager

from entity.core.context import PluginContext  # noqa: E402
from entity.core.state import PipelineState, ConversationEntry  # noqa: E402
from entity.resources import Memory  # noqa: E402
from entity.resources.interfaces.database import DatabaseResource  # noqa: E402
from entity.pipeline.errors import ResourceInitializationError  # noqa: E402
import pytest  # noqa: E402


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

    class _Cursor:
        def __init__(self, rows: list[tuple] | None = None) -> None:
            self.rows = rows or []

        def fetchone(self) -> tuple | None:
            return self.rows[0] if self.rows else None

        def fetchall(self) -> list[tuple]:
            return self.rows

    def execute(
        self, query: str, params: tuple | None = None
    ) -> "DummyConnection._Cursor":
        params = params or ()
        if query.startswith("DELETE FROM conversation_history"):
            cid = params[0] if isinstance(params, tuple) else params
            self.store.setdefault("history", {}).pop(cid, None)
            return self._Cursor()
        if query.startswith("INSERT INTO conversation_history"):
            cid, role, content, metadata, ts = params
            self.store.setdefault("history", {}).setdefault(cid, []).append(
                (role, content, json.loads(metadata), ts)
            )
            return self._Cursor()
        if query.startswith("DELETE FROM memory_kv"):
            key = params[0] if isinstance(params, tuple) else params
            self.store.setdefault("kv", {}).pop(key, None)
            return self._Cursor()
        if query.startswith("INSERT OR REPLACE INTO memory_kv") or query.startswith(
            "INSERT INTO memory_kv"
        ):
            key, value = params
            self.store.setdefault("kv", {})[key] = json.loads(value)
            return self._Cursor()
        if query.startswith("SELECT value FROM memory_kv"):
            key = params[0] if isinstance(params, tuple) else params
            value = self.store.get("kv", {}).get(key)
            return self._Cursor([(json.dumps(value),)] if value is not None else [])
        if query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            cid = params[0] if isinstance(params, tuple) else params
            rows = self.store.get("history", {}).get(cid, [])
            return self._Cursor([(r[0], r[1], json.dumps(r[2]), r[3]) for r in rows])
        return self._Cursor()

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
        if query.startswith("SELECT value FROM memory_kv"):
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
    def __init__(self, mem: Memory) -> None:
        self.resources = {"memory": mem}
        self.tools = types.SimpleNamespace()


async def make_context(tmp_path) -> PluginContext:
    state = PipelineState(conversation=[])
    db = DuckDBResource(str(tmp_path / "mem.duckdb"))
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    regs = DummyRegistries(mem)
    return PluginContext(state, regs)


@pytest.mark.asyncio
async def test_memory_roundtrip(tmp_path) -> None:
    ctx = make_context(tmp_path)
    await ctx.remember("foo", "bar")
    assert await ctx.recall("foo") == "bar"

    asyncio.run(run_test())


def test_memory_persists_between_instances() -> None:
    async def run_test() -> None:
        db = DummyDatabase()

        mem1 = Memory(config={})
        mem1.database = db
        mem1.vector_store = None
        await mem1.initialize()
        await mem1.set("foo", "bar", user_id="default")
        entry = ConversationEntry("hi", "user", datetime.now())
        await mem1.save_conversation("cid", [entry], user_id="default")

        mem2 = Memory(config={})
        mem2.database = db
        mem2.vector_store = None
        await mem2.initialize()

        assert await mem2.get("foo", user_id="default") == "bar"
        history = await mem2.load_conversation("cid", user_id="default")
        assert history == [entry]

    asyncio.run(run_test())


def test_memory_persists_with_connection_pool() -> None:
    async def run_test() -> None:
        pool = DummyPool()

        mem1 = Memory(config={})
        mem1.database = pool
        mem1.vector_store = None
        await mem1.initialize()
        await mem1.set("foo", "bar", user_id="default")
        entry = ConversationEntry("hi", "user", datetime.now())
        await mem1.save_conversation("cid", [entry], user_id="default")

        mem2 = Memory(config={})
        mem2.database = pool
        mem2.vector_store = None
        await mem2.initialize()

@pytest.mark.asyncio
async def test_initialize_without_database_raises_error() -> None:
    mem = Memory(config={})
    with pytest.raises(ResourceInitializationError):
        await mem.initialize()
