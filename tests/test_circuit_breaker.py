import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from user_plugins.failure.basic_logger import BasicLogger
from user_plugins.failure.error_formatter import ErrorFormatter


class UnstablePlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise ValueError("boom")


def make_registries():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(
            UnstablePlugin({"failure_threshold": 2, "failure_reset_timeout": 60}),
            PipelineStage.DO,
        )
    )
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    asyncio.run(
        plugins.register_plugin_for_stage(ErrorFormatter({}), PipelineStage.ERROR)
    )
    return SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)


def test_circuit_breaker_trips():
    registries = make_registries()
    asyncio.run(execute_pipeline("hi", registries))
    asyncio.run(execute_pipeline("hi", registries))
    result = asyncio.run(execute_pipeline("hi", registries))
    assert "circuit breaker" in result["error"].lower()
