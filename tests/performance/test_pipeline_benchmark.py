import asyncio

import pytest

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer


class NoOpPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        context.set_response("ok")


def _make_manager():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(NoOpPlugin({}), PipelineStage.DELIVER)
    )
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return PipelineManager(registries)


@pytest.mark.benchmark
def test_pipeline_execution_benchmark(benchmark):
    manager = _make_manager()

    def run():
        return asyncio.run(manager.run_pipeline("hi"))

    result = benchmark(run)
    assert result == "ok"
