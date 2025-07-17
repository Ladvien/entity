import pytest

from entity.core.plugins.base import Plugin, ResourcePlugin
from entity.resources.metrics import MetricsCollectorResource


class DummyPlugin(Plugin):
    stages = []

    async def _execute_impl(self, context):
        return None


class DummyResource(ResourcePlugin):
    stages = []
    name = "dummy"

    async def _execute_impl(self, context):
        return None


@pytest.mark.asyncio
async def test_plugin_lifecycle_metrics():
    plugin = DummyPlugin({})
    metrics = MetricsCollectorResource()
    plugin.metrics_collector = metrics
    await metrics.initialize()
    await plugin.initialize()
    assert plugin.is_initialized
    await plugin.shutdown()
    assert plugin.is_shutdown
    ops = await metrics.get_resource_operations()
    assert ops == []


@pytest.mark.asyncio
async def test_resource_plugin_lifecycle_metrics():
    resource = DummyResource({})
    metrics = MetricsCollectorResource()
    resource.metrics_collector = metrics
    await metrics.initialize()
    await resource.initialize()
    assert resource.is_initialized
    await resource.shutdown()
    assert resource.is_shutdown
    ops = await metrics.get_resource_operations()
    assert any(o.operation == "initialize" for o in ops)
    assert any(o.operation == "shutdown" for o in ops)
