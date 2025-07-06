import asyncio
import time

from pipeline import (
    PipelineStage,
    PluginRegistry,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.base_plugins import PluginAutoClassifier
from pipeline.context import PluginContext
from pipeline.resources import ResourceContainer


class SleepTool(ToolPlugin):
    async def execute_function(self, params):
        await asyncio.sleep(0.05)
        return params.get("text", "done")


async def use_tool_plugin(ctx: PluginContext) -> None:
    result = await ctx.use_tool("sleep", text="hello")
    ctx.set_response(result)


def make_registries() -> SystemRegistries:
    resources = ResourceContainer()
    tools = ToolRegistry()
    asyncio.run(tools.add("sleep", SleepTool({})))
    plugins = PluginRegistry()
    plugin = PluginAutoClassifier.classify(
        use_tool_plugin,
        {"stage": PipelineStage.DO, "name": "UseToolPlugin"},
    )
    asyncio.run(plugins.register_plugin_for_stage(plugin, PipelineStage.DO))
    return SystemRegistries(resources, tools, plugins)


def test_async_tool_execution():
    registries = make_registries()
    start = time.time()
    result = asyncio.run(execute_pipeline("hi", registries))
    duration = time.time() - start
    assert result == "hello"
    assert duration >= 0.05
