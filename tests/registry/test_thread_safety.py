import asyncio

from registry.registries import PluginRegistry, ResourceRegistry, ToolRegistry
from pipeline.stages import PipelineStage
from pipeline.user_plugins import PromptPlugin


class DummyPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        return None


async def test_plugin_registry_thread_safety():
    registry = PluginRegistry()

    async def register(i):
        plugin = DummyPlugin({})
        await registry.register_plugin_for_stage(plugin, PipelineStage.DO)

    await asyncio.gather(*(register(i) for i in range(10)))
    assert len(registry.get_plugins_for_stage(PipelineStage.DO)) == 10


async def test_resource_and_tool_registry_thread_safety():
    resources = ResourceRegistry()
    tools = ToolRegistry()

    async def add_resource(i):
        await resources.add(f"r{i}", object())

    async def add_tool(i):
        await tools.add(f"t{i}", object())

    await asyncio.gather(
        *(add_resource(i) for i in range(5)),
        *(add_tool(i) for i in range(5)),
    )

    assert len(resources._resources) == 5
    assert len(tools._tools) == 5
