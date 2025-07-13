import asyncio
import time

import pytest

from entity.resources import Memory, MetricsCollectorResource
from entity.resources.logging import LoggingResource
from entity.pipeline.worker import PipelineWorker
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.plugins import Plugin
from entity.core.context import PluginContext
from entity.core.stages import PipelineStage


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        failure = await context.reflect("fail_msg")
        if failure is not None:
            context.say(failure)
            return
        last = next(
            (e.content for e in reversed(context.conversation()) if e.role == "user"),
            "",
        )
        context.say(last)


class FailPlugin(Plugin):
    stages = [PipelineStage.THINK]

    def __init__(self, config: dict | None = None, *, fail: bool = True) -> None:
        super().__init__(config or {})
        self.fail = fail

    async def _execute_impl(self, context: PluginContext) -> None:
        if self.fail:
            raise RuntimeError("boom")
        await asyncio.sleep(0)


class ErrorPlugin(Plugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        await context.think("fail_msg", "failed")


@pytest.fixture()
async def registries(memory_db: Memory) -> SystemRegistries:
    metrics = MetricsCollectorResource({})
    await metrics.initialize()
    logging_res = LoggingResource({})
    await logging_res.initialize()

    class _Resources(dict):
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    resources = _Resources(
        memory=memory_db, metrics_collector=metrics, logging=logging_res
    )
    resources.get = lambda name: resources[name]

    regs = SystemRegistries(
        resources=resources,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    regs.metrics = metrics
    return regs


@pytest.mark.asyncio
async def test_standard_workflow(registries: SystemRegistries) -> None:
    plugin = EchoPlugin({})
    plugin.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(plugin, PipelineStage.OUTPUT)
    worker = PipelineWorker(registries)
    result = await worker.execute_pipeline("pipe", "hi", user_id="u1")
    assert result == "hi"


@pytest.mark.asyncio
async def test_multi_user_isolation(registries: SystemRegistries) -> None:
    plugin = EchoPlugin({})
    plugin.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(plugin, PipelineStage.OUTPUT)
    worker = PipelineWorker(registries)
    await asyncio.gather(
        worker.execute_pipeline("pipe", "one", user_id="u1"),
        worker.execute_pipeline("pipe", "two", user_id="u2"),
    )
    hist1 = await registries.resources.get("memory").load_conversation("u1_pipe")
    hist2 = await registries.resources.get("memory").load_conversation("u2_pipe")
    assert [e.content for e in hist1 if e.role == "user"] == ["one"]
    assert [e.content for e in hist2 if e.role == "user"] == ["two"]


@pytest.mark.asyncio
async def test_error_handling_and_recovery(registries: SystemRegistries) -> None:
    fail = FailPlugin({}, fail=True)
    fail.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(fail, PipelineStage.THINK)
    err = ErrorPlugin({})
    err.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(err, PipelineStage.ERROR)
    out = EchoPlugin({})
    out.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(out, PipelineStage.OUTPUT)
    worker = PipelineWorker(registries)
    fail_result = await worker.execute_pipeline("pipe", "hi", user_id="u1")
    assert fail_result == "failed"
    # Replace failing plugin with non failing
    registries.plugins = PluginRegistry()
    again = FailPlugin({}, fail=False)
    again.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(again, PipelineStage.THINK)
    out2 = EchoPlugin({})
    out2.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(out2, PipelineStage.OUTPUT)
    worker = PipelineWorker(registries)
    success = await worker.execute_pipeline("pipe", "ok", user_id="u1")
    assert success == "ok"


@pytest.mark.asyncio
async def test_performance_metrics(registries: SystemRegistries) -> None:
    plugin = EchoPlugin({})
    plugin.metrics_collector = registries.metrics
    await registries.plugins.register_plugin_for_stage(plugin, PipelineStage.OUTPUT)
    worker = PipelineWorker(registries)
    start = time.perf_counter()
    for _ in range(3):
        await worker.execute_pipeline("pipe", "hello", user_id="u1")
    elapsed = time.perf_counter() - start
    metrics = registries.metrics
    assert len(metrics.plugin_executions) == 3
    assert elapsed > 0
