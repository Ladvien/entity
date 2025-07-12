import json
import types
from contextlib import asynccontextmanager

import pytest

from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
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


class DummyConnection:
    def __init__(self, store: dict) -> None:
        self.store = store

    async def execute(self, query: str, params: tuple) -> None:
        if query.startswith("DELETE FROM conversation_history"):
            cid = params
            self.store["history"].pop(cid, None)
        elif query.startswith("INSERT INTO conversation_history"):
            cid, role, content, metadata, ts = params
            self.store.setdefault("history", {}).setdefault(cid, []).append(
                (role, content, json.loads(metadata), ts)
            )
        elif query.startswith("DELETE FROM kv_store"):
            key = params
            self.store.setdefault("kv", {}).pop(key, None)
        elif query.startswith("INSERT INTO kv_store"):
            key, value = params
            self.store.setdefault("kv", {})[key] = json.loads(value)

    async def fetch(self, query: str, params: tuple) -> list:
        if query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            cid = params
            return [
                (role, content, metadata, ts)
                for role, content, metadata, ts in self.store.get("history", {}).get(
                    cid, []
                )
            ]
        if query.startswith("SELECT value FROM kv_store"):
            key = params
            if key in self.store.get("kv", {}):
                return [(json.dumps(self.store["kv"][key]),)]
        return []


class DummyDatabase(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})
        self.data: dict = {"history": {}, "kv": {}}

    @asynccontextmanager
    async def connection(self):
        yield DummyConnection(self.data)


class DummyRegistries:
    def __init__(self) -> None:
        self.resources = {"memory": DummyMemory()}
        self.tools = types.SimpleNamespace()


class DBRegistries:
    def __init__(self) -> None:
        db = DummyDatabase()
        self.resources = {"memory": Memory(database=db, config={})}
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


@pytest.mark.asyncio
async def test_pipeline_persists_conversation(memory_db):
    regs = types.SimpleNamespace(
        resources={"memory": memory_db}, tools=types.SimpleNamespace()
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("pipe1", "hello", user_id="u1")
    await worker.execute_pipeline("pipe1", "world", user_id="u1")

    mem = regs.resources["memory"]
    history = await mem.load_conversation("u1_pipe1")
    assert [h.content for h in history] == ["hello", "world"]
