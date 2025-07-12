import asyncio
import importlib.util
import sys

import pytest
from pipeline import PipelineStage
from entity.core.plugins import ResourcePlugin

from entity.core.resources.container import ResourceContainer


class BaseRes(ResourcePlugin):
    stages = [PipelineStage.PARSE]
    name = "base"

    async def _execute_impl(self, context):
        return None


class DepRes(ResourcePlugin):
    stages = [PipelineStage.PARSE]
    name = "dep"
    dependencies = ["base"]

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self.base = None

    async def _execute_impl(self, context):
        return None


async def build_container():
    container = ResourceContainer()
    container.register("base", BaseRes, {})
    container.register("dep", DepRes, {})
    await container.build_all()
    return container


class DepInitRes(ResourcePlugin):
    stages = [PipelineStage.PARSE]
    name = "dep_init"
    dependencies = ["base"]

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self.base = None
        self.initialized_with_dep = False

    async def initialize(self) -> None:
        self.initialized_with_dep = self.base is not None

    async def _execute_impl(self, context):
        return None


def test_container_injects_dependencies():
    container = asyncio.run(build_container())
    dep = container.get("dep")
    base = container.get("base")
    assert dep.base is base


def test_health_report():
    container = asyncio.run(build_container())
    report = asyncio.run(container.health_report())
    assert report == {"base": True, "dep": True}


# Resource pool tests using dynamic import to avoid package path issues
module = importlib.import_module("entity.core.resources.container")
sys.modules["plugins.builtin.resources.container"] = module
ResourceContainerDynamic = module.ResourceContainer


class Dummy:
    def __init__(self) -> None:
        self.value = 0


async def make_resource() -> Dummy:
    return Dummy()


@pytest.mark.asyncio
async def test_pool_scales_and_metrics():
    container = ResourceContainerDynamic()
    await container.add_pool(
        "dummy",
        make_resource,
        {"min_size": 1, "max_size": 2, "scale_threshold": 0.5, "scale_step": 1},
    )
    r1 = await container.acquire("dummy")
    r2 = await container.acquire("dummy")
    metrics = container.get_metrics()["dummy"]
    assert metrics["total_size"] == 2
    await container.release("dummy", r1)
    await container.release("dummy", r2)
    metrics = container.get_metrics()["dummy"]
    assert metrics["available"] == 2


@pytest.mark.asyncio
async def test_container_async_context_shutdown():
    container = await build_container()
    async with container:
        assert container.get("base") is not None


@pytest.mark.asyncio
async def test_shutdown_order_reversed():
    log: list[str] = []

    class A(ResourcePlugin):
        async def initialize(self) -> None:
            log.append("init-a")

        async def shutdown(self) -> None:
            log.append("stop-a")

        async def _execute_impl(self, context):
            return None

    class B(ResourcePlugin):
        dependencies = ["a"]

        async def initialize(self) -> None:
            log.append("init-b")

        async def shutdown(self) -> None:
            log.append("stop-b")

        async def _execute_impl(self, context):
            return None

    container = ResourceContainer()
    container.register("a", A, {})
    container.register("b", B, {})
    await container.build_all()
    await container.shutdown_all()
    assert log == ["init-a", "init-b", "stop-b", "stop-a"]


@pytest.mark.asyncio
async def test_dependencies_injected_before_initialize():
    container = ResourceContainer()
    container.register("base", BaseRes, {})
    container.register("dep", DepInitRes, {})
    await container.build_all()
    dep = container.get("dep")
    assert dep is not None and dep.initialized_with_dep
