import types
import pytest

from entity.core.context import PluginContext
from entity.core.state import PipelineState


class DummyRegistries:
    def __init__(self, resources):
        self.resources = resources
        self.tools = types.SimpleNamespace()


def make_context():
    resources = {"memory": object(), "storage": object(), "llm": object()}
    return PluginContext(PipelineState(conversation=[]), DummyRegistries(resources))


@pytest.mark.asyncio
async def test_think_reflect_and_clear():
    ctx = make_context()
    await ctx.think("x", 1)
    assert await ctx.reflect("x") == 1
    assert ctx._state.stage_results["x"] == 1
    await ctx.clear_thoughts()
    assert await ctx.reflect("x") is None
    assert ctx._state.stage_results == {}


@pytest.mark.asyncio
async def test_advanced_temp_helpers():
    ctx = make_context()
    await ctx.advanced.think_temp("y", 2)
    assert await ctx.advanced.reflect_temp("y") == 2
    await ctx.advanced.clear_temp()
    assert await ctx.advanced.reflect_temp("y") is None


def test_get_resource_helpers():
    ctx = make_context()
    assert ctx.get_llm() is ctx.get_resource("llm")
    assert ctx.get_memory() is ctx.get_resource("memory")
    assert ctx.get_storage() is ctx.get_resource("storage")
