import asyncio

import pytest

from entity.core.resources.container import ResourceContainer
from pipeline import (PipelineStage, PluginRegistry, SystemRegistries,
                      ToolRegistry, execute_pipeline)


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

    def run():
        return asyncio.run(execute_pipeline("hi", capabilities))

    result = benchmark(run)
    assert result == "ok"
