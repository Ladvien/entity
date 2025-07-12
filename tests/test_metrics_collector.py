import pytest

from entity.core.context import PluginContext
from entity.core.plugins import Plugin, ResourcePlugin
from entity.core.registries import SystemRegistries
from entity.core.state import PipelineState
from entity.pipeline.stages import PipelineStage
from entity.resources.metrics_collector import MetricsCollectorResource


class DummyPlugin(Plugin):  # type: ignore[misc]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        await context.think("dummy", True)


class DummyResource(ResourcePlugin):  # type: ignore[misc]
    async def do_work(self, context: PluginContext) -> int:
        result: int = await self._track_operation("do_work", lambda: 1, context=context)
        return result


@pytest.mark.asyncio  # type: ignore[misc]
async def test_metrics_collection() -> None:
    metrics = MetricsCollectorResource()
    plugin = DummyPlugin()
    resource = DummyResource()
    plugin.metrics_collector = metrics
    resource.metrics_collector = metrics

    state = PipelineState(conversation=[], pipeline_id="pid")
    regs = SystemRegistries(resources={}, tools=None, plugins=None, validators=None)
    ctx = PluginContext(state, regs)
    ctx.set_current_stage(PipelineStage.THINK)

    await plugin.execute(ctx)
    await resource.do_work(ctx)

    assert metrics.plugin_metrics
    assert metrics.resource_metrics
    log = await metrics.get_unified_agent_log(pipeline_id="pid")
    assert len(log) >= 2
