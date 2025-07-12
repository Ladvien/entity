import types
import pytest

from entity.core.context import PluginContext
from entity.core.state import PipelineState


class DummyRegistries:
    def __init__(self, memory) -> None:
        self.resources = {"memory": memory}
        self.tools = types.SimpleNamespace()


def make_context(memory) -> PluginContext:
    state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries(memory))


@pytest.mark.asyncio
async def test_memory_roundtrip(memory_db) -> None:
    ctx = make_context(memory_db)
    ctx.remember("foo", "bar")

    assert ctx.memory("foo") == "bar"
    ctx2 = make_context(memory_db)
    assert ctx2.memory("foo") == "bar"
