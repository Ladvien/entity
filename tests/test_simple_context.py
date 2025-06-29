from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginRegistry,
    ResourceRegistry,
    SimpleContext,
    SystemRegistries,
    ToolRegistry,
)


def make_context():
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="test",
        metrics=MetricsCollector(),
    )
    regs = SystemRegistries(ResourceRegistry(), ToolRegistry(), PluginRegistry())
    return SimpleContext(state, regs)


def test_simple_context_methods():
    ctx = make_context()
    ctx.say("hello")
    assert ctx._state.response == "hello"

    ctx.remember("foo", "bar")
    assert ctx.recall("foo") == "bar"
    assert ctx.recall("missing", 1) == 1
