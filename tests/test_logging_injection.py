import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.resources.logging import LoggingResource
from entity.core.plugins import PromptPlugin
from entity.core.context import PluginContext
from entity.core.resources.container import ResourceContainer
from entity.core.stages import PipelineStage


class DummyPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> str:
        return "ok"


DummyPrompt.dependencies = []


@pytest.mark.asyncio
async def test_assign_shared_logging():
    container = ResourceContainer()
    LoggingResource.dependencies = []
    container.register("logging", LoggingResource, {}, layer=3)
    await container.build_all()

    init = SystemInitializer({"plugins": {}, "workflow": {}})
    plugin = DummyPrompt({})
    init._assign_shared_resources(plugin, container)

    assert plugin.logging is not None
    await container.shutdown_all()
