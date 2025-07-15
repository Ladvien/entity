import asyncio
import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin, AgentResource
from entity.pipeline.errors import InitializationError


class DummyInfra(InfrastructurePlugin):
    infrastructure_type = "infra"
    dependencies: list[str] = []
    stages: list = []


class HigherResource(AgentResource):
    dependencies: list[str] = []
    stages: list = []


class LowerInterface(ResourcePlugin):
    infrastructure_dependencies = ["infra"]
    dependencies = ["higher"]
    stages: list = []


def test_dependency_on_higher_layer_raises() -> None:
    container = ResourceContainer()
    container.register("infra", DummyInfra, {}, layer=1)
    container.register("higher", HigherResource, {}, layer=3)
    container.register("lower", LowerInterface, {}, layer=2)

    # The container validates layer rules before checking dependency order.
    with pytest.raises(InitializationError, match="layer validation"):
        asyncio.run(container.build_all())
