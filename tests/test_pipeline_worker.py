# ruff: noqa
import json
import asyncio
import types
from contextlib import asynccontextmanager

import pytest

from entity.resources import Memory
from entity.resources.interfaces.database import DatabaseResource
import entity.pipeline.utils as pipeline_utils


class StageResolver:
    @staticmethod
    def _resolve_plugin_stages(cls, config, logger=None):
        return pipeline_utils.resolve_stages(cls, config), True


pipeline_utils.StageResolver = StageResolver

from entity.pipeline import pipeline as pipeline_module  # noqa: E402
from entity.worker.pipeline_worker import PipelineWorker
from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry
from entity.pipeline.stages import PipelineStage


class DummyMemory:
    def __init__(self) -> None:
        self.loaded_id = None
        self.saved_id = None
        self.history = []

    async def load_conversation(self, pipeline_id: str, *, user_id: str = "default"):
        self.loaded_id = f"{user_id}_{pipeline_id}"
        return list(self.history)

    async def save_conversation(
        self, pipeline_id: str, history, *, user_id: str = "default"
    ):
        self.saved_id = f"{user_id}_{pipeline_id}"
        self.history = list(history)


class DummyConnection:
    def __init__(self, store: dict) -> None:
        self.store = store

    def execute(self, query: str, params: tuple | None = None):
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

    def fetch(self, query: str, params: tuple) -> list:
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

    def get_connection_pool(self):
        return DummyConnection(self.data)


class DummyRegistries:
    def __init__(self, *, plugins: PluginRegistry | None = None) -> None:
        class _Resources(dict):
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        self.resources = _Resources(memory=DummyMemory())
        self.tools = types.SimpleNamespace()
        self.validators = None
        self.plugins = plugins or PluginRegistry()


class DBRegistries:
    def __init__(self) -> None:
        db = DummyDatabase()

        class _Resources(dict):
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        mem = Memory(config={})
        mem.database = db
        mem.vector_store = None
        asyncio.run(mem.initialize())
        self.resources = _Resources(memory=mem)
        self.tools = types.SimpleNamespace()
        self.validators = None
        self.plugins = PluginRegistry()


class ThoughtPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        if await context.reflect("thought") is None:
            last = next(
                (e.content for e in context.conversation()[::-1] if e.role == "user"),
                "",
            )
            await context.think("thought", last)


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        thought = await context.reflect("thought")
        context.say(thought)


@pytest.mark.asyncio
async def test_conversation_id_generation():
    regs = DummyRegistries()
    await regs.plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.OUTPUT)
    worker = PipelineWorker(regs)
    result = await worker.execute_pipeline("pipe1", "hello", user_id="u123")

    assert result == "hello"
    mem = regs.resources["memory"]
    assert mem.loaded_id == "u123_pipe1"
    assert mem.saved_id == "u123_pipe1"


@pytest.mark.asyncio
async def test_pipeline_persists_conversation(memory_db):
    regs = types.SimpleNamespace(
        resources={"memory": memory_db},
        tools=types.SimpleNamespace(),
        plugins=PluginRegistry(),
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("pipe1", "hello", user_id="u1")
    await worker.execute_pipeline("pipe1", "world", user_id="u1")

    history = await regs.resources["memory"].load_conversation("pipe1", user_id="u1")
    assert [e.content for e in history] == ["first", "second"]


@pytest.mark.asyncio
async def test_thoughts_do_not_leak_between_executions():
    regs = DummyRegistries()
    await regs.plugins.register_plugin_for_stage(ThoughtPlugin({}), PipelineStage.THINK)
    await regs.plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.OUTPUT)

    worker = PipelineWorker(regs)

    pipeline_module.user_id = "u1"
    first = await worker.execute_pipeline("pipe1", "one", user_id="u1")
    pipeline_module.user_id = "u1"
    second = await worker.execute_pipeline("pipe1", "two", user_id="u1")

    assert first == "one"
    assert second == "two"
