import pytest

from entity.worker.pipeline_worker import PipelineWorker
from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.pipeline.stages import PipelineStage
from entity.resources.logging import LoggingResource


class EchoStorePlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        await context.remember("last", context.conversation()[-1].content)
        context.say(context.conversation()[-1].content)


@pytest.mark.asyncio
async def test_user_isolation(memory_db):
    logging_res = LoggingResource({})
    await logging_res.initialize()
    regs = SystemRegistries(
        resources={"memory": memory_db, "logging": logging_res},
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    await regs.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "hello", user_id="alice")
    await worker.execute_pipeline("chat", "world", user_id="bob")

    hist_a = await memory_db.load_conversation("chat", user_id="alice")
    hist_b = await memory_db.load_conversation("chat", user_id="bob")

    assert [e.content for e in hist_a if e.role == "user"] == ["hello"]
    assert [e.content for e in hist_b if e.role == "user"] == ["world"]
    assert await memory_db.get("last", user_id="alice") == "hello"
    assert await memory_db.get("last", user_id="bob") == "world"


@pytest.mark.asyncio
async def test_history_persists_per_user(memory_db):
    logging_res = LoggingResource({})
    await logging_res.initialize()
    regs = SystemRegistries(
        resources={"memory": memory_db, "logging": logging_res},
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    await regs.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "one", user_id="alice")
    await worker.execute_pipeline("chat", "two", user_id="bob")
    await worker.execute_pipeline("chat", "three", user_id="alice")

    hist_a = await memory_db.load_conversation("chat", user_id="alice")
    hist_b = await memory_db.load_conversation("chat", user_id="bob")

    assert [e.content for e in hist_a if e.role == "user"] == ["one", "three"]
    assert [e.content for e in hist_b if e.role == "user"] == ["two"]


@pytest.mark.asyncio
async def test_cross_user_access_denied(memory_db):
    logging_res = LoggingResource({})
    await logging_res.initialize()
    regs = SystemRegistries(
        resources={"memory": memory_db, "logging": logging_res},
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    await regs.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "secret", user_id="alice")

    hist = await memory_db.load_conversation("chat", user_id="bob")
    assert hist == []
    assert await memory_db.get("last", user_id="bob") is None


@pytest.mark.asyncio
async def test_persistent_storage_is_isolated(memory_db):
    await memory_db.store_persistent("token", "A", user_id="alice")
    await memory_db.store_persistent("token", "B", user_id="bob")

    assert await memory_db.fetch_persistent("token", user_id="alice") == "A"
    assert await memory_db.fetch_persistent("token", user_id="bob") == "B"


@pytest.mark.asyncio
async def test_batch_store_and_delete_scoped_by_user(memory_db):
    await memory_db.batch_store({"a": 1, "b": 2}, user_id="alice")
    await memory_db.batch_store({"a": 3}, user_id="bob")

    await memory_db.delete_persistent("a", user_id="bob")

    assert await memory_db.fetch_persistent("a", user_id="alice") == 1
    assert await memory_db.fetch_persistent("b", user_id="alice") == 2
    assert await memory_db.fetch_persistent("a", user_id="bob") is None
    assert await memory_db.fetch_persistent("b", user_id="bob") is None
