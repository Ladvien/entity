import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

from entity.core.resources.container import ResourceContainer
from entity.core.state import MetricsCollector
from entity.resources.memory import Memory
from pipeline import (
    ConversationEntry,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from user_plugins.prompts.complex_prompt import ComplexPrompt


class FakeLLM:
    name = "llm"

    def __init__(self):
        self.generate = AsyncMock(return_value="done")


class FakeMemory(Memory):
    def __init__(self, history):
        super().__init__(config={})
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
    resources = ResourceContainer()
    asyncio.run(resources.add("llm", llm))
    asyncio.run(resources.add("memory", memory))
    capabilities = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, capabilities)


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
