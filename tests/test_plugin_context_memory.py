import asyncio
from datetime import datetime
import pytest
from entity.core.state import ConversationEntry
from entity.resources import Memory
from entity.pipeline.errors import ResourceInitializationError
from tests.utils import make_async_context


async def run_test(memory: Memory) -> None:
    mem1 = memory
    await mem1.set("foo", "bar", user_id="default")
    entry = ConversationEntry("hi", "user", datetime.now())
    await mem1.save_conversation("cid", [entry], user_id="default")

    mem2 = Memory({})
    mem2.database = mem1.database
    mem2.vector_store = None
    await mem2.initialize()

    assert await mem2.get("foo", user_id="default") == "bar"
    history = await mem2.load_conversation("cid")
    assert history == [entry]


@pytest.mark.asyncio
async def test_memory_roundtrip(memory_db: Memory) -> None:
    ctx = await make_async_context(memory=memory_db)
    await ctx.remember("foo", "bar")
    assert await ctx.recall("foo") == "bar"

    await run_test(memory_db)


def test_memory_persists_between_instances(memory_db: Memory) -> None:
    asyncio.run(run_test(memory_db))


@pytest.mark.asyncio
async def test_initialize_without_database_raises_error() -> None:
    mem = Memory({})
    with pytest.raises(ResourceInitializationError):
        await mem.initialize()
