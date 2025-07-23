import asyncio
import pytest

from entity.plugins.context import PluginContext


@pytest.mark.asyncio
async def test_remember_isolated_by_user_id():
    shared = {}
    ctx_a = PluginContext({}, user_id="a", memory=shared)
    ctx_b = PluginContext({}, user_id="b", memory=shared)

    await ctx_a.remember("val", 1)
    await ctx_b.remember("val", 2)

    assert await ctx_a.recall("val") == 1
    assert await ctx_b.recall("val") == 2
    assert shared == {"a:val": 1, "b:val": 2}
