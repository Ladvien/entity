import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.errors import ErrorResponse

from entity.core.resources.container import ResourceContainer
from user_plugins.failure.basic_logger import BasicLogger
from user_plugins.failure.error_formatter import ErrorFormatter


class UnstablePlugin(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        raise ValueError("boom")


def make_capabilities():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(
            UnstablePlugin({"failure_threshold": 2, "failure_reset_timeout": 60}),
            PipelineStage.OUTPUT,
        )
    )
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    asyncio.run(
        plugins.register_plugin_for_stage(ErrorFormatter({}), PipelineStage.OUTPUT)
    )
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_circuit_breaker_trips():
    capabilities = make_capabilities()
    asyncio.run(execute_pipeline("hi", capabilities))
    asyncio.run(execute_pipeline("hi", capabilities))
    result = asyncio.run(execute_pipeline("hi", capabilities))
    assert isinstance(result, ErrorResponse)
    assert "circuit breaker" in result.error.lower()
