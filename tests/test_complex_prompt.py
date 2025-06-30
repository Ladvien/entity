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
from pipeline.plugins.prompts.complex_prompt import ComplexPrompt


class FakeLLM:
    name = "ollama"

    def __init__(self):
        self.generate = AsyncMock(return_value="done")


class FakeDB:
    name = "database"

    def __init__(self, history):
        self.load_history = AsyncMock(return_value=history)


class FakeVectorMemory:
    name = "vector_memory"

    def __init__(self):
        self.add_embedding = AsyncMock()
        self.query_similar = AsyncMock(return_value=["similar"])


def make_context(llm, db, memory):
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hello", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceRegistry()
    resources.add("ollama", llm)
    resources.add("database", db)
    resources.add("vector_memory", memory)
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_complex_prompt_uses_resources():
    llm = FakeLLM()
    history = [ConversationEntry(content="old", role="user", timestamp=datetime.now())]
    db = FakeDB(history)
    memory = FakeVectorMemory()
    state, ctx = make_context(llm, db, memory)
    plugin = ComplexPrompt({"k": 1})

    asyncio.run(plugin.execute(ctx))

    db.load_history.assert_awaited_with("1")
    memory.add_embedding.assert_awaited_with("hello")
    memory.query_similar.assert_awaited_with("hello", 1)
    llm.generate.assert_awaited()
    assert state.response == "done"
    assert any(
        e.role == "assistant" and e.content == "done" for e in state.conversation
    )
