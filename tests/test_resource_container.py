import importlib.util
import sys
from types import ModuleType
from pathlib import Path

import pytest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "pipeline.resources.container",
    root / "src/pipeline/resources/container.py",
)
sys.modules["pipeline"] = ModuleType("pipeline")
sys.modules["pipeline.resources"] = ModuleType("pipeline.resources")
module = importlib.util.module_from_spec(spec)
sys.modules["pipeline.resources.container"] = module
spec.loader.exec_module(module)  # type: ignore[arg-type]
ResourceContainer = module.ResourceContainer


class Dummy:
    def __init__(self) -> None:
        self.value = 0


async def make_resource() -> Dummy:
    return Dummy()


@pytest.mark.asyncio
async def test_pool_scales_and_metrics():
    container = ResourceContainer()
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
