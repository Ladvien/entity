import types
import pytest

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.core.stages import PipelineStage
from entity.core.plugins import Plugin
from entity.resources.metrics import MetricsCollectorResource
from entity.core.resources.container import ResourceContainer
from entity.core.registries import SystemRegistries, ToolRegistry


class DummyPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> str:
        return "ok"


@pytest.mark.asyncio
async def test_plugin_dependencies_include_metrics():
    assert "metrics_collector?" in DummyPlugin.dependencies


@pytest.mark.asyncio
async def test_plugin_metrics_success():
    metrics = MetricsCollectorResource({})
    await metrics.initialize()
    plugin = DummyPlugin({})
    container = ResourceContainer()
    await container.add("metrics_collector", metrics)
    plugin.metrics_collector = metrics
    registries = SystemRegistries(
        resources=container, tools=ToolRegistry(), plugins=PluginRegistry()
    )
    state = PipelineState(conversation=[], pipeline_id="123")
    context = PluginContext(state, registries)
    context.set_current_stage(PipelineStage.THINK)

    await plugin.execute(context)

    records = await metrics.get_plugin_executions()
    assert len(records) == 1
    record = records[0]
    assert record.success is True
    assert record.plugin_name == "DummyPlugin"


@pytest.mark.asyncio
async def test_plugin_metrics_failure():
    class FailPlugin(DummyPlugin):
        async def _execute_impl(self, context: PluginContext) -> None:
            raise RuntimeError("boom")

    metrics = MetricsCollectorResource({})
    await metrics.initialize()
    plugin = FailPlugin({})
    container = ResourceContainer()
    await container.add("metrics_collector", metrics)
    plugin.metrics_collector = metrics
    registries = SystemRegistries(
        resources=container, tools=ToolRegistry(), plugins=PluginRegistry()
    )
    state = PipelineState(conversation=[], pipeline_id="123")
    context = PluginContext(state, registries)
    context.set_current_stage(PipelineStage.THINK)

    with pytest.raises(RuntimeError):
        await plugin.execute(context)

    records = await metrics.get_plugin_executions()
    assert len(records) == 1
    record = records[0]
    assert record.success is False
    assert record.error_type == "RuntimeError"
