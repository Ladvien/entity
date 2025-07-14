import pytest

from entity.core.plugins import InfrastructurePlugin
from entity.core.resources.container import ResourceContainer
from entity.resources.base import AgentResource as CanonicalBase
from entity.pipeline.errors import InitializationError


class SimpleInfra(InfrastructurePlugin):
    infrastructure_type = "infra"
    stages: list = []
    dependencies: list = []


SimpleInfra.dependencies = []


class CanonicalRes(CanonicalBase):
    stages: list = []
    dependencies: list = []


CanonicalRes.dependencies = []


class CustomRes:
    stages: list = []
    dependencies = ["infra"]


class NoDepRes:
    stages: list = []
    dependencies: list = []


class CycleA:
    stages: list = []
    dependencies = ["b"]


class CycleB:
    stages: list = []
    dependencies = ["c"]


class CycleC:
    stages: list = []
    dependencies = ["a"]


@pytest.mark.asyncio
async def test_invalid_layer_number():
    container = ResourceContainer()
    container.register("bad", SimpleInfra, {}, layer=5)
    with pytest.raises(InitializationError, match="Invalid layer"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_mismatched_class_layer():
    container = ResourceContainer()
    container.register("canon", CanonicalRes, {}, layer=2)
    with pytest.raises(InitializationError, match="infrastructure_dependencies"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_dependency_layer_violation():
    container = ResourceContainer()
    container.register("infra", SimpleInfra, {}, layer=1)
    container.register("custom", CustomRes, {}, layer=4)
    with pytest.raises(InitializationError, match="layer rules"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_custom_no_dep_allowed_in_layer3():
    container = ResourceContainer()
    container.register("nodep", NoDepRes, {}, layer=3)
    container._validate_layers()


@pytest.mark.asyncio
async def test_cycle_detection():
    container = ResourceContainer()
    container.register("a", CycleA, {}, layer=4)
    container.register("b", CycleB, {}, layer=4)
    with pytest.raises(InitializationError, match="not registered"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_long_cycle_detection():
    container = ResourceContainer()
    container.register("a", CycleA, {}, layer=4)
    container.register("b", CycleB, {}, layer=4)
    container.register("c", CycleC, {}, layer=4)
    with pytest.raises(InitializationError, match="Circular dependency") as exc:
        container._validate_layers()
    assert set(exc.value.name.split(", ")) == {"a", "b"}
