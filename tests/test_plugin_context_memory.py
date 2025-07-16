import asyncio
from datetime import datetime
import pytest
from entity.core.context import PluginContext
from entity.core.state import PipelineState, ConversationEntry
from entity.resources import Memory
from entity.pipeline.errors import ResourceInitializationError
from entity.core.resources.container import ResourceContainer
from entity.core.registries import SystemRegistries, ToolRegistry, PluginRegistry


async def make_context(memory: Memory) -> PluginContext:
    regs = SystemRegistries(
        resources=ResourceContainer(),
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    await regs.resources.add("memory", memory)
    return PluginContext(PipelineState(conversation=[]), regs)


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
    ctx = await make_context(memory_db)
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
