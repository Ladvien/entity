import asyncio
from datetime import datetime

from plugins.contrib.prompts.memory_retrieval import MemoryRetrievalPrompt

from pipeline import (ConversationEntry, MetricsCollector, PipelineState,
                      PluginContext, PluginRegistry, ResourceContainer,
                      SystemRegistries, ToolRegistry)
from pipeline.resources.memory_resource import (MemoryResource,
                                                SimpleMemoryResource)


class DummyMemory(MemoryResource):
    def __init__(self, history):
        super().__init__(None, None, {})
        self.history = history

    async def load_conversation(self, conversation_id: str):
        return self.history

    async def save_conversation(self, conversation_id: str, entries):
        self.history = entries


def make_context(memory: MemoryResource | None = None):
    past = [
        ConversationEntry(
            content="past message", role="assistant", timestamp=datetime.now()
        )
    ]
    memory = memory or SimpleMemoryResource()
    asyncio.run(memory.save_conversation("1", past))
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", memory))

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


def test_prompt_accepts_custom_memory():
    custom = DummyMemory([])
    state, ctx = make_context(custom)
    plugin = MemoryRetrievalPrompt({})

    asyncio.run(plugin.execute(ctx))

    assert len(state.conversation) == 2
