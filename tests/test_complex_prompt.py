import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

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
from pipeline.resources.memory_resource import MemoryResource
from user_plugins.prompts.complex_prompt import ComplexPrompt


class FakeLLM:
    name = "llm"

    def __init__(self):
        self.generate = AsyncMock(return_value="done")


class FakeMemory(MemoryResource):
    def __init__(self, history):
        super().__init__(None, None, {})
        self._history = history

    async def load_conversation(self, conversation_id: str):
        return self._history

    async def search_similar(self, query: str, k: int = 5):
        return ["similar"]

    async def save_conversation(self, conversation_id: str, history):
        self._history = history


def make_context(llm, memory):
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hello", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceRegistry()
    asyncio.run(resources.add("llm", llm))
    asyncio.run(resources.add("memory", memory))
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_complex_prompt_uses_resources():
    llm = FakeLLM()
    history = [ConversationEntry(content="old", role="user", timestamp=datetime.now())]
    memory = FakeMemory(history)
    state, ctx = make_context(llm, memory)
    plugin = ComplexPrompt({"k": 1})

    asyncio.run(plugin.execute(ctx))

    llm.generate.assert_awaited()
    assert state.response == "done"
    assert any(
        e.role == "assistant" and e.content == "done" for e in state.conversation
    )
