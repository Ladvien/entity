import asyncio

import pytest

from entity.core.resources.container import ResourceContainer
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class NoOpPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        context.set_response("ok")


def _make_capabilities():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(NoOpPlugin({}), PipelineStage.DELIVER)
    )
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


@pytest.mark.benchmark
def test_pipeline_execution_benchmark(benchmark):
    caps = _make_capabilities()

    def run():
        return asyncio.run(execute_pipeline("hi", caps))

    result = benchmark(run)
    assert result == "ok"
