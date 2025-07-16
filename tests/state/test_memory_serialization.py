from datetime import datetime

import pytest

from tests.conftest import AsyncPGDatabase
from entity.resources import Memory
from entity.core.state import ConversationEntry, PipelineState, ToolCall


@pytest.fixture()
async def memory(postgres_dsn: str) -> Memory:
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


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
