import types
from datetime import datetime

from entity.core.context import PluginContext
from entity.core.state import ConversationEntry, PipelineState


class DummyRegistries:
    def __init__(self):
        self.resources = {}
        self.tools = types.SimpleNamespace()


def make_context(state=None):
    if state is None:
        state = PipelineState(conversation=[])
    return PluginContext(state, DummyRegistries())


def test_replace_conversation_history():
    ctx = make_context()
    new_history = [
        ConversationEntry("hi", "user", datetime.now()),
        ConversationEntry("hello", "assistant", datetime.now()),
    ]
    ctx.advanced.replace_conversation_history(new_history)

    assert ctx.get_conversation_history() == new_history


def test_update_response():
    state = PipelineState(conversation=[], response="foo")
    ctx = make_context(state)
    ctx.update_response(lambda r: r + "bar")

    assert ctx.response == "foobar"
