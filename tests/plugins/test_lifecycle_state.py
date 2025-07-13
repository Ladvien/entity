import pytest

from entity.core.plugins import Plugin, ResourcePlugin


class DummyPlugin(Plugin):
    stages = []

    def __init__(self, config=None):
        super().__init__(config or {})
        self.events = []

    async def _execute_impl(self, context):
        return None

    async def _on_initialize(self) -> None:
        self.events.append("init")

    async def _on_shutdown(self) -> None:
        self.events.append("shutdown")


class DummyResource(ResourcePlugin):
    stages = []
    name = "dummy"

    def __init__(self, config=None):
        super().__init__(config or {})
        self.events = []

    async def _execute_impl(self, context):
        return None

    async def _on_initialize(self) -> None:
        self.events.append("init")

    async def _on_shutdown(self) -> None:
        self.events.append("shutdown")


@pytest.mark.asyncio
async def test_plugin_lifecycle_state():
    plugin = DummyPlugin({})
    await plugin.initialize()
    await plugin.initialize()
    assert plugin.is_initialized

    await plugin.shutdown()
    await plugin.shutdown()
    assert plugin.is_shutdown
    assert plugin.events == ["init", "shutdown"]


@pytest.mark.asyncio
async def test_resource_plugin_lifecycle_state():
    resource = DummyResource({})
    await resource.initialize()
    await resource.initialize()
    assert resource.is_initialized

    await resource.shutdown()
    await resource.shutdown()
    assert resource.is_shutdown
    assert resource.events == ["init", "shutdown"]
