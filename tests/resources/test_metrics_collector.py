import pytest

from entity.core.stages import PipelineStage
from entity.resources.metrics import MetricsCollectorResource


@pytest.mark.asyncio
async def test_unified_agent_log() -> None:
    metrics = MetricsCollectorResource({})
    await metrics.initialize()

    await metrics.record_plugin_execution(
        pipeline_id="agent1",
        stage=PipelineStage.INPUT,
        plugin_name="PluginA",
        duration_ms=1.0,
        success=True,
    )
    await metrics.record_resource_operation(
        pipeline_id="agent1",
        resource_name="memory",
        operation="read",
        duration_ms=2.0,
        success=True,
    )

    log = await metrics.get_unified_agent_log("agent1")
    types = {entry["type"] for entry in log}
    assert {"plugin", "resource"} == types


@pytest.mark.asyncio
async def test_performance_summary() -> None:
    metrics = MetricsCollectorResource({})
    await metrics.initialize()

    await metrics.record_plugin_execution(
        pipeline_id="agent1",
        stage=PipelineStage.INPUT,
        plugin_name="PluginA",
        duration_ms=10.0,
        success=True,
    )
    await metrics.record_plugin_execution(
        pipeline_id="agent1",
        stage=PipelineStage.INPUT,
        plugin_name="PluginA",
        duration_ms=20.0,
        success=False,
    )
    await metrics.record_plugin_execution(
        pipeline_id="agent1",
        stage=PipelineStage.THINK,
        plugin_name="PluginB",
        duration_ms=15.0,
        success=True,
    )

    summary = await metrics.get_performance_summary("agent1")
    assert summary["runs"] == 3
    assert summary["plugins"]["PluginA"]["success_rate"] == pytest.approx(0.5)
    assert summary["plugins"]["PluginB"]["average_duration_ms"] == pytest.approx(15.0)
