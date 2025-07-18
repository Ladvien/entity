from datetime import datetime
import pytest

from entity.core.state import ConversationEntry, PipelineState
from tests.utils import make_async_context, make_context


class DummyTool:
    async def execute_function(self, params):
        return params


@pytest.mark.asyncio
async def test_replace_conversation_history():
    ctx = await make_async_context()
    new_history = [
        ConversationEntry("hi", "user", datetime.now()),
        ConversationEntry("hello", "assistant", datetime.now()),
    ]
    await ctx.advanced.replace_conversation_history(new_history)

    assert ctx.get_conversation_history() == new_history


def test_update_response():
    state = PipelineState(conversation=[], response="foo")
    ctx = make_context(state=state)
    ctx.update_response(lambda r: r + "bar")

    assert ctx.response == "foobar"


@pytest.mark.asyncio
async def test_queue_tool_use():
    state = PipelineState(conversation=[])
    tool = DummyTool()
    ctx = await make_async_context(state=state, tools={"dummy": tool.execute_function})

    key1 = await ctx.advanced.queue_tool_use("dummy", x=1)
    key2 = await ctx.advanced.queue_tool_use("dummy", x=2)

    assert key1 == "dummy_0"
    assert key2 == "dummy_1"
    assert len(state.pending_tool_calls) == 2
