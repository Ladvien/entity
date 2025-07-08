from experiments.unified_registry.resource_manager import (
    AsyncResourceManager,
    BaseResource,
)


class DummyResource(BaseResource):
    def __init__(self) -> None:
        self.initialized = False
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def shutdown(self) -> None:
        self.closed = True

    async def health_check(self) -> bool:
        return self.initialized and not self.closed


async def test_manager_lifecycle():
    manager = AsyncResourceManager()
    await manager.register("dummy", DummyResource())
    await manager.initialize_all()
    report = await manager.health_report()
    assert report == {"dummy": True}
    await manager.shutdown_all()
    assert manager.get("dummy").closed
    assert manager.metrics.resources_initialized == 1
