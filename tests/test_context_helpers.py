import pytest
from tests.utils import make_context


@pytest.mark.asyncio
async def test_think_reflect_and_clear(pg_memory, clear_pg_memory):
    ctx = make_context(memory=pg_memory)
    await ctx.think("x", 1)
    assert await ctx.reflect("x") == 1
    assert ctx._state.stage_results["x"] == 1
    await ctx.clear_thoughts()
    assert await ctx.reflect("x") is None
    assert ctx._state.stage_results == {}


@pytest.mark.asyncio
async def test_advanced_temp_helpers(pg_memory, clear_pg_memory):
    ctx = make_context(memory=pg_memory)
    await ctx.advanced.think_temp("y", 2)
    assert await ctx.advanced.reflect_temp("y") == 2
    assert ctx._state.temporary_thoughts["y"] == 2
    await ctx.advanced.clear_temp()
    assert await ctx.advanced.reflect_temp("y") is None
    assert ctx._state.temporary_thoughts == {}


def test_get_resource_helpers(pg_memory):
    ctx = make_context(memory=pg_memory)
    assert ctx.get_llm() is ctx.get_resource("llm")
    assert ctx.get_memory() is ctx.get_resource("memory")
    assert ctx.get_storage() is ctx.get_resource("storage")
