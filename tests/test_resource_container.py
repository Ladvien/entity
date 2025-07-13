import asyncio
import pytest

from entity.core.resources.container import ResourceContainer
from entity.pipeline.errors import InitializationError
from entity.core.plugins import InfrastructurePlugin, ResourcePlugin, AgentResource
from entity.resources.logging import LoggingResource


class InfraPlugin(InfrastructurePlugin):
    infrastructure_type = "infra"
    stages: list = []
    dependencies: list = []

    def __init__(self, config=None):
        super().__init__(config or {})
        self.initialized = False
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def shutdown(self) -> None:
        self.closed = True


class InterfacePlugin(ResourcePlugin):
    infrastructure_dependencies = ["infra"]
    stages: list = []
    dependencies: list = []

    def __init__(self, config=None):
        super().__init__(config or {})
        self.infra: InfraPlugin | None = None
        self.initialized = False

    async def initialize(self) -> None:
        self.initialized = True


class CanonicalResource(AgentResource):
    dependencies = ["iface"]
    stages: list = []

    def __init__(self, config=None):
        super().__init__(config or {})
        self.iface: InterfacePlugin | None = None
        self.initialized = False
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def shutdown(self) -> None:
        self.closed = True


InfraPlugin.dependencies = []
InterfacePlugin.dependencies = []
CanonicalResource.dependencies = ["iface"]

LoggingResource.dependencies = []


@pytest.mark.asyncio
async def test_container_lifecycle_and_order():
    container = ResourceContainer()
    container.register("infra", InfraPlugin, {}, layer=1)
    container.register("iface", InterfacePlugin, {}, layer=2)
    container.register("canon", CanonicalResource, {}, layer=3)

    await container.build_all()

    infra = container.get("infra")
    iface = container.get("iface")
    canon = container.get("canon")

    assert infra.initialized
    assert iface.initialized
    assert iface.infra is infra
    assert canon.initialized
    assert canon.iface is iface

    await container.shutdown_all()
    assert canon.closed
    assert infra.closed


def test_layer_violation():
    class BadResource(AgentResource):
        dependencies = ["infra"]
        stages: list = []

    BadResource.dependencies = ["infra"]

    container = ResourceContainer()
    container.register("infra", InfraPlugin, {}, layer=1)
    container.register("bad", BadResource, {}, layer=3)

    with pytest.raises(InitializationError, match="layer validation"):
        asyncio.run(container.build_all())


def test_missing_interface_dependencies():
    class BadInterface(ResourcePlugin):
        stages: list = []
        dependencies: list = []

    BadInterface.dependencies = []

    container = ResourceContainer()
    container.register("infra", InfraPlugin, {}, layer=1)
    container.register("iface", BadInterface, {}, layer=2)

    with pytest.raises(InitializationError, match="infrastructure_dependencies"):
        asyncio.run(container.build_all())


def test_missing_infrastructure_type():
    class BadInfra(InfrastructurePlugin):
        stages: list = []
        dependencies: list = []

    BadInfra.dependencies = []

    container = ResourceContainer()
    container.register("bad", BadInfra, {}, layer=1)

    with pytest.raises(InitializationError, match="infrastructure_type"):
        asyncio.run(container.build_all())


@pytest.mark.asyncio
async def test_health_check_failure_on_build():
    class UnhealthyResource(AgentResource):
        dependencies: list[str] = []
        stages: list = []

        async def health_check(self) -> bool:
            return False

    UnhealthyResource.dependencies = []

    container = ResourceContainer()
    container.register("bad", UnhealthyResource, {}, layer=3)

    with pytest.raises(InitializationError, match="health check"):
        await container.build_all()


events: list[str] = []


class RestartableResource(AgentResource):
    dependencies: list[str] = []
    stages: list = []

    async def initialize(self) -> None:
        events.append("init")

    async def shutdown(self) -> None:
        events.append("shutdown")

    async def restart(self) -> None:
        events.append("restart")
        await super().restart()


RestartableResource.dependencies = []


@pytest.mark.asyncio
async def test_restart_resource():
    container = ResourceContainer()
    container.register("res", RestartableResource, {}, layer=3)

    await container.build_all()
    first = container.get("res")

    await container.restart_resource("res")

    second = container.get("res")
    assert first is second
    assert events == ["init", "restart", "shutdown", "init"]
