import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    ResourcePlugin,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.base_plugins import PluginAutoClassifier
from pipeline.context import PluginContext

from entity.core.resources.container import ResourceContainer


class MyResource(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        context.set_metadata("init", True)


class MyTool(ToolPlugin):
    required_params = ["value"]

    async def execute_function(self, params):
        return params["value"]


async def my_prompt(ctx: PluginContext) -> None:
    val = await ctx.tool_use("tool", value="ok")
    ctx.set_response(val)


def make_capabilities() -> SystemRegistries:
    resources = ResourceContainer()
    asyncio.run(resources.add("resource", MyResource({})))
    tools = ToolRegistry()
    asyncio.run(tools.add("tool", MyTool({})))
    plugins = PluginRegistry()
    plugin = PluginAutoClassifier.classify(
        my_prompt,
        {"stage": PipelineStage.DELIVER, "name": "MyPrompt"},
    )
    asyncio.run(plugins.register_plugin_for_stage(plugin, PipelineStage.DELIVER))
    return SystemRegistries(resources, tools, plugins)


def test_plugin_layers_cooperate():
    capabilities = make_capabilities()
    result = asyncio.run(execute_pipeline("hi", capabilities))
    assert result == "ok"
