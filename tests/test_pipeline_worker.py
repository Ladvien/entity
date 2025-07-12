import types
import pytest

from pipeline import PipelineWorker
from entity.resources.memory import Memory
from entity.core.registries import SystemRegistries


class DummyRegistries:
    def __init__(self, memory: Memory) -> None:
        self.resources = {"memory": memory}
        self.plugins = types.SimpleNamespace()
        self.tools = types.SimpleNamespace()


@pytest.mark.asyncio
async def test_conversation_persists_across_workers() -> None:
    memory = Memory(config={})
    resources = {"memory": memory}
    regs = SystemRegistries(
        resources=resources,
        tools=types.SimpleNamespace(),
        plugins=types.SimpleNamespace(),
    )

    worker1 = PipelineWorker(regs)
    await worker1.execute_pipeline("chat", "Hello")

    history = await memory.load_conversation("chat")
    assert len(history) == 1
    assert history[0].content == "Hello"

    worker2 = PipelineWorker(regs)
    await worker2.execute_pipeline("chat", "How are you?")

    history = await memory.load_conversation("chat")
    assert len(history) == 2
    assert history[0].content == "Hello"
    assert history[1].content == "How are you?"
