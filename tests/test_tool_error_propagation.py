import asyncio

from user_plugins.failure.basic_logger import BasicLogger
from user_plugins.failure.error_formatter import ErrorFormatter

<<<<<<< HEAD
from pipeline import (PipelineStage, PluginRegistry, PromptPlugin,
                      ResourceContainer, SystemRegistries, ToolPlugin,
                      ToolRegistry, execute_pipeline)
=======
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.resources import ResourceContainer
>>>>>>> 842b365f2ee0307cf77e24d7bdb710602bc576a8


class FailingTool(ToolPlugin):
    async def execute_function(self, params):
        raise RuntimeError("tool boom")


class CallToolPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.execute_tool("fail", {})


def make_registries():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(CallToolPlugin({}), PipelineStage.DO)
    plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR)
    plugins.register_plugin_for_stage(ErrorFormatter({}), PipelineStage.ERROR)

    tools = ToolRegistry()
    tools.add("fail", FailingTool({"max_retries": 0}))

    return SystemRegistries(ResourceContainer(), tools, plugins)


def test_tool_failure_propagates_to_error_stage():
    registries = make_registries()
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == {"error": "fail failed (RuntimeError): tool boom"}
