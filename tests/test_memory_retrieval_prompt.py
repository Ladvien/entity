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
from pipeline.plugins.prompts.memory_retrieval import MemoryRetrievalPrompt
from pipeline.plugins.resources.memory_resource import SimpleMemoryResource


def make_context():
    past = [
        ConversationEntry(
            content="past message", role="assistant", timestamp=datetime.now()
        )
    ]
    memory = SimpleMemoryResource()
    memory.set("history", past)
    resources = ResourceRegistry()
    resources.add("memory", memory)

    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        metrics=MetricsCollector(),
        pipeline_id="1",
    )
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_retrieved_history_appended():
    state, ctx = make_context()
    plugin = MemoryRetrievalPrompt({})

    asyncio.run(plugin.execute(ctx))

    assert len(state.conversation) == 2
    assert state.conversation[-1].content == "past message"
