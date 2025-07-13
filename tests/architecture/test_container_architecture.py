import asyncio
import pytest

from entity.core.resources.container import ResourceContainer, DependencyGraph
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin, AgentResource
from entity.pipeline.errors import InitializationError


class SimpleInfra(InfrastructurePlugin):
    infrastructure_type = "infra"
    stages: list = []
    dependencies: list = []


SimpleInfra.dependencies = []


class OtherInfra(InfrastructurePlugin):
    infrastructure_type = "other"
    stages: list = []
    dependencies: list = []


OtherInfra.dependencies = []


class BadInterface(ResourcePlugin):
    stages: list = []
    dependencies: list = []


BadInterface.dependencies = []


class CustomResource(AgentResource):
    stages: list = []
    dependencies = []


CustomResource.dependencies = []


def test_layer1_missing_infrastructure_type():
    class BadInfra(InfrastructurePlugin):
        stages: list = []
        dependencies: list = []

    BadInfra.dependencies = []

    container = ResourceContainer()
    container.register("bad", BadInfra, {}, layer=1)

    with pytest.raises(InitializationError, match="infrastructure_type"):
        asyncio.run(container.build_all())


def test_layer1_with_dependencies():
    class DepInfra(InfrastructurePlugin):
        infrastructure_type = "dep"
        stages: list = []
        dependencies = ["other"]

    DepInfra.dependencies = ["other"]

    container = ResourceContainer()
    container.register("other", OtherInfra, {}, layer=1)
    container.register("bad", DepInfra, {}, layer=1)

    with pytest.raises(InitializationError, match="cannot have dependencies"):
        asyncio.run(container.build_all())


def test_layer2_missing_infrastructure_dependencies():
    container = ResourceContainer()
    container.register("infra", SimpleInfra, {}, layer=1)
    container.register("iface", BadInterface, {}, layer=2)

    with pytest.raises(InitializationError, match="infrastructure_dependencies"):
        asyncio.run(container.build_all())


def test_dependency_graph_cycle_detection():
    graph = {"a": ["b"], "b": ["a"]}
    dg = DependencyGraph(graph)
    with pytest.raises(InitializationError, match="Circular dependency detected"):
        dg.topological_sort()
