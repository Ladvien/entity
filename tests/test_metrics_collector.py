import types
import pytest

import sys
import pathlib
import types

import pytest

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.core.stages import PipelineStage
from entity.core.plugins import Plugin
from entity.resources.metrics import MetricsCollectorResource


class DummyPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> str:
        return "ok"


@pytest.mark.asyncio
async def test_plugin_dependencies_include_metrics():
    assert "metrics_collector" in DummyPlugin.dependencies


@pytest.mark.asyncio
async def test_plugin_metrics_success():
    metrics = MetricsCollectorResource({})
    plugin = DummyPlugin({})
    plugin.metrics_collector = metrics
    registries = types.SimpleNamespace(
        resources=types.SimpleNamespace(get=lambda _n: None),
        tools=types.SimpleNamespace(),
        plugins=None,
        validators=None,
    )
    state = PipelineState(conversation=[], pipeline_id="123")
    context = PluginContext(state, registries)
    context.set_current_stage(PipelineStage.THINK)

    await plugin.execute(context)

    assert len(metrics.plugin_executions) == 1
    record = metrics.plugin_executions[0]
    assert record.success is True
    assert record.plugin_name == "DummyPlugin"


@pytest.mark.asyncio
async def test_plugin_metrics_failure():
    class FailPlugin(DummyPlugin):
        async def _execute_impl(self, context: PluginContext) -> None:
            raise RuntimeError("boom")

    metrics = MetricsCollectorResource({})
    plugin = FailPlugin({})
    plugin.metrics_collector = metrics
    registries = types.SimpleNamespace(
        resources=types.SimpleNamespace(get=lambda _n: None),
        tools=types.SimpleNamespace(),
        plugins=None,
        validators=None,
    )
    state = PipelineState(conversation=[], pipeline_id="123")
    context = PluginContext(state, registries)
    context.set_current_stage(PipelineStage.THINK)

    with pytest.raises(RuntimeError):
        await plugin.execute(context)

    assert len(metrics.plugin_executions) == 1
    record = metrics.plugin_executions[0]
    assert record.success is False
    assert record.error_type == "RuntimeError"
