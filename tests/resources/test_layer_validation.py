import pytest
from entity.core.resources.container import ResourceContainer
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin, AgentResource
from entity.pipeline.errors import InitializationError


class Infra(InfrastructurePlugin):
    infrastructure_type = "db"
    stages: list = []
    dependencies: list = []


class Higher(AgentResource):
    __module__ = "tests.resources"
    stages: list = []
    dependencies: list = []


class Interface(ResourcePlugin):
    stages: list = []
    infrastructure_dependencies = ["infra"]
    dependencies = ["higher"]


class CycleA:
    stages: list = []
    dependencies = ["cycle_b"]


class CycleB:
    stages: list = []
    dependencies = ["cycle_a"]


@pytest.mark.asyncio
async def test_one_layer_step_rule(monkeypatch):
    monkeypatch.setattr(Infra, "dependencies", [])
    monkeypatch.setattr(Higher, "dependencies", [])
    container = ResourceContainer()
    container.register("infra", Infra, {}, layer=1)
    container.register("higher", Higher, {}, layer=3)
    container.register("iface", Interface, {}, layer=2)
    with pytest.raises(InitializationError, match="layer rules"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_cycle_detection_error(monkeypatch):
    monkeypatch.setattr(CycleA, "dependencies", ["cycle_b"])
    monkeypatch.setattr(CycleB, "dependencies", ["cycle_a"])
    monkeypatch.setattr(CycleA, "__module__", "tests.resources")
    monkeypatch.setattr(CycleB, "__module__", "tests.resources")
    container = ResourceContainer()
    container.register("cycle_a", CycleA, {}, layer=4)
    container.register("cycle_b", CycleB, {}, layer=4)
    with pytest.raises(InitializationError, match="Circular dependency") as exc:
        container._validate_layers()
    assert "cycle_a -> cycle_b -> cycle_a" in str(exc.value)
