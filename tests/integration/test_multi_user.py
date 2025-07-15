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
async def test_user_isolation(pg_memory):
    logging_res = LoggingResource({})
    await logging_res.initialize()
    regs = SystemRegistries(
        resources={"memory": pg_memory, "logging": logging_res},
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

    hist_a = await pg_memory.load_conversation("chat", user_id="alice")
    hist_b = await pg_memory.load_conversation("chat", user_id="bob")

    assert [e.content for e in hist_a if e.role == "user"] == ["hello"]
    assert [e.content for e in hist_b if e.role == "user"] == ["world"]
    assert await pg_memory.get("last", user_id="alice") == "hello"
    assert await pg_memory.get("last", user_id="bob") == "world"


@pytest.mark.asyncio
async def test_history_persists_per_user(pg_memory):
    logging_res = LoggingResource({})
    await logging_res.initialize()
    regs = SystemRegistries(
        resources={"memory": pg_memory, "logging": logging_res},
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

    hist_a = await pg_memory.load_conversation("chat", user_id="alice")
    hist_b = await pg_memory.load_conversation("chat", user_id="bob")

    assert [e.content for e in hist_a if e.role == "user"] == ["one", "three"]
    assert [e.content for e in hist_b if e.role == "user"] == ["two"]


@pytest.mark.asyncio
async def test_cross_user_access_denied(pg_memory):
    logging_res = LoggingResource({})
    await logging_res.initialize()
    regs = SystemRegistries(
        resources={"memory": pg_memory, "logging": logging_res},
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    await regs.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "secret", user_id="alice")

    hist = await pg_memory.load_conversation("chat", user_id="bob")
    assert hist == []
    assert await pg_memory.get("last", user_id="bob") is None


@pytest.mark.asyncio
async def test_persistent_storage_is_isolated(pg_memory):
    await pg_memory.store_persistent("token", "A", user_id="alice")
    await pg_memory.store_persistent("token", "B", user_id="bob")

    assert await pg_memory.fetch_persistent("token", user_id="alice") == "A"
    assert await pg_memory.fetch_persistent("token", user_id="bob") == "B"


@pytest.mark.asyncio
async def test_batch_store_and_delete_scoped_by_user(pg_memory):
    await pg_memory.batch_store({"a": 1, "b": 2}, user_id="alice")
    await pg_memory.batch_store({"a": 3}, user_id="bob")

    await pg_memory.delete_persistent("a", user_id="bob")

    assert await pg_memory.fetch_persistent("a", user_id="alice") == 1
    assert await pg_memory.fetch_persistent("b", user_id="alice") == 2
    assert await pg_memory.fetch_persistent("a", user_id="bob") is None
    assert await pg_memory.fetch_persistent("b", user_id="bob") is None


@pytest.mark.asyncio
async def test_multiple_workers_same_user(pg_memory):
    """Two workers should handle requests for one user interchangeably."""
    logging_res = LoggingResource({})
    await logging_res.initialize()

    regs1 = SystemRegistries(
        resources={"memory": pg_memory, "logging": logging_res},
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    await regs1.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker1 = PipelineWorker(regs1)

    regs2 = SystemRegistries(
        resources={"memory": pg_memory, "logging": logging_res},
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    await regs2.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker2 = PipelineWorker(regs2)

    await worker1.execute_pipeline("chat", "hello", user_id="alice")
    await worker2.execute_pipeline("chat", "again", user_id="alice")

    hist = await pg_memory.load_conversation("chat", user_id="alice")
    assert [e.content for e in hist if e.role == "user"] == ["hello", "again"]
    assert await pg_memory.get("last", user_id="alice") == "again"
