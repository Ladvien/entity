import json
import types
from contextlib import asynccontextmanager

import pytest

from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
from pipeline.worker import PipelineWorker


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
        return []


class DummyDatabase(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})
        self.data: dict = {"history": {}}

    @asynccontextmanager
    async def connection(self):
        yield DummyConnection(self.data)


class DummyRegistries:
    def __init__(self, db: DummyDatabase) -> None:
        self.resources = {"memory": Memory(database=db, config={})}
        self.tools = types.SimpleNamespace()


@pytest.mark.asyncio
async def test_workers_share_state_across_instances() -> None:
    db = DummyDatabase()

    regs1 = DummyRegistries(db)
    worker1 = PipelineWorker(regs1)
    await worker1.execute_pipeline("pipe", "hello", user_id="u1")

    regs2 = DummyRegistries(db)
    worker2 = PipelineWorker(regs2)
    await worker2.execute_pipeline("pipe", "there", user_id="u1")

    history = await regs2.resources["memory"].load_conversation("u1_pipe")
    assert [e.content for e in history] == ["hello", "there"]


@pytest.mark.asyncio
async def test_worker_does_not_cache_state() -> None:
    db = DummyDatabase()
    regs = DummyRegistries(db)
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("pipe", "first", user_id="u1")
    await worker.execute_pipeline("pipe", "second", user_id="u1")

    history = await regs.resources["memory"].load_conversation("u1_pipe")
    assert [e.content for e in history] == ["first", "second"]
