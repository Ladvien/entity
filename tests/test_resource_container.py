import asyncio

from pipeline import PipelineStage
from pipeline.plugins import ResourcePlugin
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
