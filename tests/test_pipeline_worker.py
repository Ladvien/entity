import types
import pytest

from pipeline.worker import PipelineWorker


class DummyMemory:
    def __init__(self) -> None:
        self.loaded_id = None
        self.saved_id = None
        self.history = []

    async def load_conversation(self, conversation_id: str):
        self.loaded_id = conversation_id
        return list(self.history)

    async def save_conversation(self, conversation_id: str, history):
        self.saved_id = conversation_id
        self.history = list(history)


class DummyRegistries:
    def __init__(self) -> None:
        self.resources = {"memory": DummyMemory()}
        self.tools = types.SimpleNamespace()


@pytest.mark.asyncio
async def test_conversation_id_generation():
    regs = DummyRegistries()
    worker = PipelineWorker(regs)
    result = await worker.execute_pipeline("pipe1", "hello", user_id="u123")

    assert result == "hello"
    mem = regs.resources["memory"]
    assert mem.loaded_id == "u123_pipe1"
    assert mem.saved_id == "u123_pipe1"
