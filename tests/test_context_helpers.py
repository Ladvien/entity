import types

from entity.core.context import PluginContext
from entity.core.state import PipelineState


class DummyRegistries:
    def __init__(self, resources):
        self.resources = resources
        self.tools = types.SimpleNamespace()


def make_context():
    resources = {"memory": object(), "storage": object(), "llm": object()}
    return PluginContext(PipelineState(conversation=[]), DummyRegistries(resources))


def test_get_resource_helpers():
    ctx = make_context()
    assert ctx.get_llm() is ctx.get_resource("llm")
    assert ctx.get_memory() is ctx.get_resource("memory")
    assert ctx.get_storage() is ctx.get_resource("storage")
