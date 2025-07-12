import types
import duckdb
from contextlib import asynccontextmanager

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource


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
