import asyncio

import pytest
from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)

from entity.core.resources.container import ResourceContainer


class RespondPlugin:
    stages = [PipelineStage.DELIVER]

    async def execute(self, context):
        context.set_response("ok")


@pytest.mark.benchmark
def test_full_pipeline_benchmark(benchmark):
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(RespondPlugin(), PipelineStage.DELIVER)
    )
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    manager = PipelineManager(capabilities)

    def run():
        return asyncio.run(manager.run_pipeline("hi"))

    result = benchmark(run)
    assert result == "ok"
