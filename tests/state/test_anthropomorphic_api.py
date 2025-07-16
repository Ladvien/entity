import types

import pytest

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory
from entity.core.resources.container import ResourceContainer
from entity.core.registries import SystemRegistries, ToolRegistry, PluginRegistry


@pytest.fixture()
async def context(memory_db: Memory) -> PluginContext:
    container = ResourceContainer()
    await container.add("memory", memory_db)
    regs = SystemRegistries(
        resources=container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    return PluginContext(PipelineState(conversation=[]), regs)


@pytest.mark.asyncio
async def test_remember_recall_interop(context: PluginContext) -> None:
    await context.remember("foo", "bar")
    assert await context._memory.fetch_persistent("foo", user_id="default") == "bar"
    await context._memory.store_persistent("baz", 123, user_id="default")
    assert await context.recall("baz") == 123


@pytest.mark.asyncio
async def test_think_reflect_roundtrip(context: PluginContext) -> None:
    await context.think("idea", 42)
    assert await context.reflect("idea") == 42
