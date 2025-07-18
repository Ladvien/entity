import pytest
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.worker.pipeline_worker import PipelineWorker


@pytest.mark.asyncio
async def test_workers_share_state_across_instances(
    pg_container: ResourceContainer,
) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    worker1 = PipelineWorker(regs)
    await worker1.execute_pipeline("pipe", "hello", user_id="u1")

    worker2 = PipelineWorker(regs)
    await worker2.execute_pipeline("pipe", "there", user_id="u1")

    memory = pg_container.get("memory")
    history = await memory.load_conversation("pipe", user_id="u1")
    assert [e.content for e in history] == ["hello", "there"]


@pytest.mark.asyncio
async def test_worker_does_not_cache_state(pg_container: ResourceContainer) -> None:
    regs = SystemRegistries(
        resources=pg_container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("pipe", "first", user_id="u1")
    await worker.execute_pipeline("pipe", "second", user_id="u1")

    memory = pg_container.get("memory")
    history = await memory.load_conversation("pipe", user_id="u1")
    assert [e.content for e in history] == ["first", "second"]
