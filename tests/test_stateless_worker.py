import asyncio
import json
import types
from contextlib import asynccontextmanager

import pytest

from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
from entity.pipeline.worker import PipelineWorker
from entity.core.registries import PluginRegistry


class DummyConnection:
    def __init__(self, store: dict) -> None:
        self.store = store
        self._last_result: list | None = None

    def execute(self, query: str, params: tuple | None = None) -> None:
        if query.startswith("DELETE FROM conversation_history"):
            cid = params[0]
            self.store["history"].pop(cid, None)
        elif query.startswith("INSERT INTO conversation_history"):
            cid, role, content, metadata, ts = params
            self.store.setdefault("history", {}).setdefault(cid, []).append(
                (role, content, json.loads(metadata), ts)
            )
        elif query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            cid = params[0]
            self._last_result = [
                (role, content, json.dumps(metadata), ts)
                for role, content, metadata, ts in self.store.get("history", {}).get(
                    cid, []
                )
            ]
        return self

    def fetch(self, query: str, params: tuple) -> list:
        if query.startswith(
            "SELECT role, content, metadata, timestamp FROM conversation_history"
        ):
            cid = params[0]
            return [
                (role, content, metadata, ts)
                for role, content, metadata, ts in self.store.get("history", {}).get(
                    cid, []
                )
            ]
        return []

    def fetchall(self) -> list:
        return self._last_result or []


class DummyDatabase(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})
        self.data: dict = {"history": {}}

    @asynccontextmanager
    async def connection(self):
        yield DummyConnection(self.data)

    def get_connection_pool(self):
        return DummyConnection(self.data)


class DummyRegistries:
    def __init__(
        self, db: DummyDatabase, *, plugins: PluginRegistry | None = None
    ) -> None:
        mem = Memory(config={})
        mem.database = db
        mem.vector_store = None
        self.resources = {"memory": mem}
        self.tools = types.SimpleNamespace()
        self.plugins = plugins or PluginRegistry()


@pytest.mark.asyncio
async def test_workers_share_state_across_instances() -> None:
    db = DummyDatabase()

    regs1 = DummyRegistries(db)
    await regs1.resources["memory"].initialize()
    worker1 = PipelineWorker(regs1)
    await worker1.execute_pipeline("pipe", "hello", user_id="u1")

    regs2 = DummyRegistries(db)
    await regs2.resources["memory"].initialize()
    worker2 = PipelineWorker(regs2)
    await worker2.execute_pipeline("pipe", "there", user_id="u1")

    history = await regs2.resources["memory"].load_conversation("pipe", user_id="u1")
    assert [e.content for e in history] == ["hello", "there"]


@pytest.mark.asyncio
async def test_worker_does_not_cache_state() -> None:
    db = DummyDatabase()
    regs = DummyRegistries(db)
    await regs.resources["memory"].initialize()
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("pipe", "first", user_id="u1")
    await worker.execute_pipeline("pipe", "second", user_id="u1")

    history = await regs.resources["memory"].load_conversation("pipe", user_id="u1")
    assert [e.content for e in history] == ["first", "second"]
