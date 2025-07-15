import types
from datetime import datetime
import pytest

from entity.core.context import PluginContext
from entity.core.state import ConversationEntry, PipelineState


class DummyTool:
    async def execute_function(self, params):
        return params


class DummyRegistries:
    def __init__(self):
        self.resources = {}
        tool = DummyTool()
        self.tools = types.SimpleNamespace(
            get=lambda name: tool if name == "dummy" else None,
            discover=lambda **filters: [("dummy", tool)],
        )


def make_context(state=None):
    if state is None:
        state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries())


@pytest.mark.asyncio
async def test_replace_conversation_history():
    ctx = make_context()
    new_history = [
        ConversationEntry("hi", "user", datetime.now()),
        ConversationEntry("hello", "assistant", datetime.now()),
    ]
    await ctx.advanced.replace_conversation_history(new_history)

    assert ctx.get_conversation_history() == new_history


def test_update_response():
    state = PipelineState(conversation=[], response="foo")
    ctx = make_context(state)
    ctx.update_response(lambda r: r + "bar")

    assert ctx.response == "foobar"


@pytest.mark.asyncio
async def test_queue_tool_use_via_property_and_wrapper():
    state = PipelineState(conversation=[])
    ctx = make_context(state)

    key1 = await ctx.advanced.queue_tool_use("dummy", x=1)
    key2 = await ctx.queue_tool_use("dummy", x=2)

    assert key1 == "dummy_0"
    assert key2 == "dummy_1"
    assert len(state.pending_tool_calls) == 2
