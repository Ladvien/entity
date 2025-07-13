import pytest

from entity.core.plugins import InfrastructurePlugin, ResourcePlugin
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


@pytest.mark.asyncio
async def test_invalid_layer_number():
    container = ResourceContainer()
    container.register("bad", SimpleInfra, {}, layer=5)
    with pytest.raises(InitializationError, match="Invalid layer"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_mismatched_class_layer():
    container = ResourceContainer()
    container.register("canon", CanonicalRes, {}, layer=3)
    with pytest.raises(InitializationError, match="Incorrect layer"):
        container._validate_layers()


@pytest.mark.asyncio
async def test_dependency_layer_violation():
    container = ResourceContainer()
    container.register("infra", SimpleInfra, {}, layer=1)
    container.register("custom", CustomRes, {}, layer=4)
    with pytest.raises(InitializationError, match="layer rules"):
        container._validate_layers()
