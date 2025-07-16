import types
import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import AgentResource
from entity.resources.logging import LoggingResource
from entity.resources.metrics import MetricsCollectorResource
from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.core.registries import SystemRegistries, ToolRegistry, PluginRegistry


class DummyResource(AgentResource):
    stages: list = []


DummyResource.dependencies = []
LoggingResource.dependencies = []
MetricsCollectorResource.dependencies = []


@pytest.mark.asyncio
async def test_custom_resource_access():
    container = ResourceContainer()
    DummyResource.dependencies = []
    container.register("chat_gpt", DummyResource, {}, layer=4)

    await container.build_all()
    dummy = container.get("chat_gpt")

    registries = SystemRegistries(
        resources=container,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
    )
    context = PluginContext(PipelineState(conversation=[]), registries)

    assert context.get_resource("chat_gpt") is dummy

    await container.shutdown_all()
