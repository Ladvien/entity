import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin
from entity.infrastructure import DuckDBInfrastructure
from entity.resources.base import AgentResource


events: list[str] = []


class Infra(InfrastructurePlugin):
    infrastructure_type = "infra"
    stages: list = []
    dependencies: list = []

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.initialized = False
        self.shutdown_calls = 0

    async def initialize(self) -> None:
        events.append("init:infra")
        self.initialized = True

    async def shutdown(self) -> None:
        events.append("shutdown:infra")
        self.shutdown_calls += 1


class Interface(ResourcePlugin):
    infrastructure_dependencies = ["infra"]
    stages: list = []
    dependencies: list = []

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.initialized = False
        self.infra: Infra | None = None

    async def initialize(self) -> None:
        events.append("init:iface")
        self.initialized = True


class FailingResource(AgentResource):
    __module__ = "entity.resources.tests"
    dependencies = ["iface"]
    stages: list = []

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.iface: Interface | None = None
        self.healthy = True

    async def initialize(self) -> None:
        events.append("init:failing")

    async def shutdown(self) -> None:
        events.append("shutdown:failing")

    async def health_check(self) -> bool:
        return self.healthy


Infra.dependencies = []
Interface.dependencies = []
FailingResource.dependencies = ["iface"]


@pytest.mark.asyncio
async def test_lifecycle_order_and_restart():
    container = ResourceContainer()
    container.register("database_backend", DuckDBInfrastructure, {}, layer=1)
    container.register("infra", Infra, {}, layer=1)
    container.register("iface", Interface, {}, layer=2)
    container.register("fail", FailingResource, {}, layer=3)

    await container.build_all()

    assert (
        events.index("init:infra")
        < events.index("init:iface")
        < events.index("init:failing")
    )

    failing: FailingResource = container.get("fail")  # type: ignore
    failing.healthy = False
    await container.restart_failed()

    assert events.count("init:failing") == 2
    assert events.count("shutdown:failing") == 1

    failing = container.get("fail")  # after restart
    failing.healthy = False
    await container.shutdown_all()

    # restarted once more during shutdown then shut down
    assert events.count("init:failing") == 3
    assert events.count("shutdown:failing") == 3
