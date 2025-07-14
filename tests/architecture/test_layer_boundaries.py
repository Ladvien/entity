import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin
from entity.resources.base import AgentResource
from entity.pipeline.errors import InitializationError


class Infra(InfrastructurePlugin):
    infrastructure_type = "db"
    stages: list = []
    dependencies: list = []


class Interface(ResourcePlugin):
    infrastructure_dependencies = ["db"]
    stages: list = []
    dependencies: list = []


class BadResource(AgentResource):
    dependencies = ["db"]
    stages: list = []


class CanonA(AgentResource):
    __module__ = "entity.resources.tests"
    dependencies = ["iface"]
    stages: list = []


class CanonB(AgentResource):
    __module__ = "entity.resources.tests"
    dependencies = ["canon_a"]
    stages: list = []


Infra.dependencies = []
Interface.dependencies = []
BadResource.dependencies = ["db"]


@pytest.mark.asyncio
async def test_layer_boundary_violation() -> None:
    container = ResourceContainer()
    container.register("db", Infra, {}, layer=1)
    container.register("iface", Interface, {}, layer=2)
    container.register("bad", BadResource, {}, layer=4)

    with pytest.raises(InitializationError, match="one-layer step"):
        await container.build_all()


@pytest.mark.asyncio
async def test_layer_three_dependency_on_same_layer() -> None:
    container = ResourceContainer()
    container.register("db", Infra, {}, layer=1)
    container.register("iface", Interface, {}, layer=2)
    container.register("canon_a", CanonA, {}, layer=3)
    container.register("canon_b", CanonB, {}, layer=3)

    with pytest.raises(InitializationError, match="one-layer step"):
        await container.build_all()
