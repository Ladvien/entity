import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from pipeline import PipelineStage
from pipeline.base_plugins import ResourcePlugin
from pipeline.resources import ResourceContainer


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
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "plugins.builtin.resources.container",
    root / "plugins.builtin.resources/container.py",
)

_orig_pipeline = sys.modules.get("pipeline")
_orig_resources = sys.modules.get("plugins.builtin.resources")

module = importlib.util.module_from_spec(spec)
sys.modules["plugins.builtin.resources.container"] = module
try:
    sys.modules["pipeline"] = ModuleType("pipeline")
    sys.modules["plugins.builtin.resources"] = ModuleType("plugins.builtin.resources")
    spec.loader.exec_module(module)  # type: ignore[arg-type]
finally:
    if _orig_pipeline is not None:
        sys.modules["pipeline"] = _orig_pipeline
    else:
        sys.modules.pop("pipeline", None)

    if _orig_resources is not None:
        sys.modules["plugins.builtin.resources"] = _orig_resources
    else:
        sys.modules.pop("plugins.builtin.resources", None)

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
