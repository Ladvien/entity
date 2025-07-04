import asyncio
from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.user_plugins.prompts.pii_scrubber import PIIScrubberPrompt


def make_context():
    state = PipelineState(
        conversation=[
            ConversationEntry(
                content="Email me at user@example.com or call 555-111-2222",
                role="user",
                timestamp=datetime.now(),
            )
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    state.response = "Contact admin@example.com at (123) 456-7890"
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_pii_is_scrubbed_from_history_and_response():
    state, ctx = make_context()
    plugin = PIIScrubberPrompt({})

    asyncio.run(plugin.execute(ctx))

    assert "user@example.com" not in state.conversation[0].content
    assert "555-111-2222" not in state.conversation[0].content
    assert "admin@example.com" not in state.response
    assert "123" not in state.response
    assert "[email]" in state.conversation[0].content
    assert "[phone]" in state.conversation[0].content
    assert "[email]" in state.response
    assert "[phone]" in state.response
