import types
import pytest

from entity.core.resources.container import ResourceContainer
from entity.resources import AgentResource
from entity.resources.logging import LoggingResource
from entity.core.context import PluginContext
from entity.core.state import PipelineState


class DummyResource(AgentResource):
    stages: list = []


DummyResource.dependencies = []
LoggingResource.dependencies = []


@pytest.mark.asyncio
async def test_custom_resource_access():
    container = ResourceContainer()
    DummyResource.dependencies = []
    container.register("chat_gpt", DummyResource, {}, layer=3)

    await container.build_all()
    dummy = container.get("chat_gpt")

    registries = types.SimpleNamespace(
        resources=container, tools=types.SimpleNamespace()
    )
    context = PluginContext(PipelineState(conversation=[]), registries)

    assert context.get_resource("chat_gpt") is dummy

    await container.shutdown_all()
