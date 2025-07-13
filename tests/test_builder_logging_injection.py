import pytest
from entity.core.agent import _AgentBuilder
from entity.core.plugins import PromptPlugin
from entity.resources.logging import LoggingResource
from entity.resources.metrics import MetricsCollectorResource
from entity.core.stages import PipelineStage


class DummyPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "ok"


DummyPrompt.dependencies = []


@pytest.mark.asyncio
async def test_builder_assigns_logging():
    builder = _AgentBuilder()
    container = builder.resource_registry
    LoggingResource.dependencies = []
    MetricsCollectorResource.dependencies = []
    container.register("logging", LoggingResource, {}, layer=3)
    container.register("metrics_collector", MetricsCollectorResource, {}, layer=3)
    await builder.add_plugin(DummyPrompt({}))
    await builder.build_runtime()
    plugin = builder._added_plugins[0]
    assert plugin.logging is not None
    assert plugin.metrics_collector is not None
    await container.shutdown_all()
