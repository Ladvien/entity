import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    ResourcePlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.base_plugins import PluginAutoClassifier
from pipeline.context import PluginContext


class MyResource(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        context.set_metadata("init", True)


class MyTool(ToolPlugin):
    required_params = ["value"]

    async def execute_function(self, params):
        return params["value"]


async def my_prompt(ctx: PluginContext) -> None:
    val = await ctx.use_tool("tool", value="ok")
    ctx.set_response(val)


def make_registries() -> SystemRegistries:
    resources = ResourceRegistry()
    resources.add("resource", MyResource({}))
    tools = ToolRegistry()
    tools.add("tool", MyTool({}))
    plugins = PluginRegistry()
    plugin = PluginAutoClassifier.classify(
        my_prompt,
        {"stage": PipelineStage.DO, "name": "MyPrompt"},
    )
    plugins.register_plugin_for_stage(plugin, PipelineStage.DO)
    return SystemRegistries(resources, tools, plugins)


def test_plugin_layers_cooperate():
    registries = make_registries()
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == "ok"
