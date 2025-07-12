import asyncio
import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin, AgentResource
from entity.pipeline.errors import InitializationError


class DummyInfra(InfrastructurePlugin):
    infrastructure_type = "infra"
    stages: list = []


class HigherResource(AgentResource):
    stages: list = []


class LowerInterface(ResourcePlugin):
    infrastructure_dependencies = ["infra"]
    dependencies = ["higher"]
    stages: list = []


def test_dependency_on_higher_layer_raises(monkeypatch) -> None:
    monkeypatch.setattr(DummyInfra, "dependencies", [])
    monkeypatch.setattr(HigherResource, "dependencies", [])
    monkeypatch.setattr(LowerInterface, "dependencies", ["higher"])
    container = ResourceContainer()
    container.register("infra", DummyInfra, {}, layer=1)
    container.register("higher", HigherResource, {}, layer=3)
    container.register("lower", LowerInterface, {}, layer=2)

    with pytest.raises(InitializationError, match="layer rules"):
        asyncio.run(container.build_all())
