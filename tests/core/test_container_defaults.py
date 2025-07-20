import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import AgentResource
from entity.core.plugins import InfrastructurePlugin
from entity.resources.logging import LoggingResource
from entity.resources.metrics import MetricsCollectorResource


class DummyDatabase(InfrastructurePlugin):
    infrastructure_type = "database"
    stages: list = []
    dependencies: list = []


class DummyResource(AgentResource):
    __module__ = "entity.resources.tests"
    dependencies: list[str] = []
    stages: list = []

    def __init__(self, config=None):
        super().__init__(config or {})
        self.initialized = False

    async def initialize(self) -> None:
        self.initialized = True


DummyDatabase.dependencies = []
DummyResource.dependencies = []
LoggingResource.dependencies = []
MetricsCollectorResource.dependencies = []


@pytest.mark.asyncio
async def test_build_all_adds_defaults():
    container = ResourceContainer()
    container.register("database_backend", DummyDatabase, {}, layer=1)
    container.register("dummy", DummyResource, {}, layer=4)

    await container.build_all()

    assert container.get("logging") is not None
    assert container.get("metrics_collector") is not None
    assert container._layers["metrics_collector"] == 3

    await container.shutdown_all()
