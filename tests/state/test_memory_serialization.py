import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
import pytest

from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
from entity.core.state import ConversationEntry, PipelineState, ToolCall


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


@pytest.fixture()
async def memory() -> Memory:
    mem = Memory(config={})
    mem.database = InMemoryDB()
    mem.vector_store = None
    await mem.initialize()
    yield mem


def _create_state() -> PipelineState:
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )
    state.stage_results["x"] = 1
    state.pending_tool_calls.append(ToolCall(name="t", params={"a": 1}, result_key="r"))
    return state


@pytest.mark.asyncio
async def test_pipeline_state_roundtrip(memory: Memory) -> None:
    state = _create_state()
    data = state.to_dict()
    await memory.set("state", data)
    loaded = await memory.get("state")
    assert loaded == data
