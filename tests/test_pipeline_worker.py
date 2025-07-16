import pytest
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.plugins import Plugin
from entity.core.resources.container import ResourceContainer
from entity.pipeline.stages import PipelineStage
from entity.worker.pipeline_worker import PipelineWorker


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
        if thought is None:
            thought = context.conversation()[-1].content
        context.say(thought)


class EchoStorePlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        await context.remember("last", context.conversation()[-1].content)
        context.say(context.conversation()[-1].content)


@pytest.mark.asyncio
async def test_conversation_id_generation(pg_container: ResourceContainer) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    await regs.plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.OUTPUT)
    worker = PipelineWorker(regs)
    result = await worker.execute_pipeline("pipe1", "hello", user_id="u123")

    assert result == "hello"
    async with pg_container.get("database").connection() as conn:  # type: ignore[union-attr]
        convo_ids = {
            row[0]
            for row in await conn.fetch(
                "SELECT conversation_id FROM conversation_history", ()
            )
        }
    assert "u123_pipe1" in convo_ids


@pytest.mark.asyncio
async def test_pipeline_persists_conversation(pg_container: ResourceContainer) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("pipe1", "hello", user_id="u1")
    await worker.execute_pipeline("pipe1", "world", user_id="u1")

    memory = pg_container.get("memory")
    history = await memory.load_conversation("pipe1", user_id="u1")
    assert [e.content for e in history] == ["hello", "world"]


@pytest.mark.asyncio
async def test_thoughts_do_not_leak_between_executions(
    pg_container: ResourceContainer,
) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    await regs.plugins.register_plugin_for_stage(ThoughtPlugin({}), PipelineStage.THINK)
    await regs.plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.OUTPUT)

    worker = PipelineWorker(regs)

    first = await worker.execute_pipeline("pipe1", "one", user_id="u1")
    second = await worker.execute_pipeline("pipe1", "two", user_id="u1")

    assert first == "one"
    assert second == "two"


@pytest.mark.asyncio
async def test_conversation_and_memory_namespaces(
    pg_container: ResourceContainer,
) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    await regs.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "hi", user_id="alice")

    async with pg_container.get("database").connection() as conn:  # type: ignore[union-attr]
        convo_ids = {
            row[0]
            for row in await conn.fetch(
                "SELECT conversation_id FROM conversation_history", ()
            )
        }
        kv_keys = {row[0] for row in await conn.fetch("SELECT key FROM memory_kv", ())}

    assert convo_ids == {"alice_chat"}
    assert kv_keys == {"alice:last"}


@pytest.mark.asyncio
async def test_user_data_isolated(pg_container: ResourceContainer) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    await regs.plugins.register_plugin_for_stage(
        EchoStorePlugin({}), PipelineStage.OUTPUT
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "hello", user_id="alice")
    await worker.execute_pipeline("chat", "world", user_id="bob")

    memory = pg_container.get("memory")
    hist_a = await memory.load_conversation("chat", user_id="alice")
    hist_b = await memory.load_conversation("chat", user_id="bob")

    assert hist_a[0].content == "hello"
    assert hist_b[0].content == "world"
    assert await memory.get("last", user_id="alice") == "hello"
    assert await memory.get("last", user_id="bob") == "world"
