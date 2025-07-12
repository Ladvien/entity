import types

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.resources import Memory


class DummyRegistries:
    def __init__(self) -> None:
        self.resources = {"memory": Memory(config={})}
        self.tools = types.SimpleNamespace()


def make_context() -> PluginContext:
    state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries())


def test_memory_roundtrip() -> None:
    ctx = make_context()
    ctx.remember("foo", "bar")

    assert ctx.memory("foo") == "bar"
