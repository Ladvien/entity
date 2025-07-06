import asyncio

import pytest

<<<<<<< HEAD
from pipeline import (PipelineManager, PipelineStage, PluginRegistry,
                      ResourceContainer, SystemRegistries, ToolRegistry)
=======
from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
>>>>>>> 842b365f2ee0307cf77e24d7bdb710602bc576a8


class RespondPlugin:
    stages = [PipelineStage.DO]

    async def execute(self, context):
        context.set_response("ok")


@pytest.mark.benchmark
def test_full_pipeline_benchmark(benchmark):
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(RespondPlugin(), PipelineStage.DO)
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)

    def run():
        return asyncio.run(manager.run_pipeline("hi"))

    result = benchmark(run)
    assert result == "ok"
