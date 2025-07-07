import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.errors import ErrorResponse
from pipeline.resources import ResourceContainer
from user_plugins.failure.basic_logger import BasicLogger
from user_plugins.failure.error_formatter import ErrorFormatter


class FailingTool(ToolPlugin):
    async def execute_function(self, params):
        raise RuntimeError("tool boom")


class CallToolPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.execute_tool("fail", {})


def make_registries():
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(CallToolPlugin({}), PipelineStage.DO))
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    asyncio.run(
        plugins.register_plugin_for_stage(ErrorFormatter({}), PipelineStage.ERROR)
    )

    tools = ToolRegistry()
    tools.add("fail", FailingTool({"max_retries": 0}))

    return SystemRegistries(ResourceContainer(), tools, plugins)


def test_tool_failure_propagates_to_error_stage():
    registries = make_registries()
    result = asyncio.run(execute_pipeline("hi", registries))
    assert isinstance(result, ErrorResponse)
    data = result.to_dict()
    assert data["error"] == "tool boom"
    assert data["plugin"] == "fail"
    assert data["stage"] == "do"
    assert data["type"] == "plugin_error"
