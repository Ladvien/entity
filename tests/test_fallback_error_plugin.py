import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)

from entity.core.resources.container import ResourceContainer
from user_plugins.failure.basic_logger import BasicLogger


class FailPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise RuntimeError("boom")


def make_capabilities():
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(FailPlugin({}), PipelineStage.DO))
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_fallback_error_plugin_sets_response():
    capabilities = make_capabilities()
    result = asyncio.run(execute_pipeline("hi", capabilities))
    assert result["type"] == "static_fallback"
