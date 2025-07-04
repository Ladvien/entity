import asyncio

from pipeline import (PipelineStage, PluginRegistry, PromptPlugin,
                      ResourceRegistry, SystemRegistries, ToolRegistry,
                      execute_pipeline)
from pipeline.resources.memory import Memory
from pipeline.resources.memory_resource import SimpleMemoryResource


class IncrementPlugin(PromptPlugin):
    stages = [PipelineStage.DO]
    dependencies = ["memory"]

    async def _execute_impl(self, context):
        memory: Memory = context.get_resource("memory")
        count = memory.get("count", 0) + 1
        memory.set("count", count)
        context.set_response(count)


def make_registries():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(IncrementPlugin({}), PipelineStage.DO)
    resources = ResourceRegistry()
    resources.add("memory", SimpleMemoryResource())
    return SystemRegistries(resources, ToolRegistry(), plugins)


def test_memory_persists_between_runs():
    registries = make_registries()
    first = asyncio.run(execute_pipeline("hi", registries))
    second = asyncio.run(execute_pipeline("again", registries))
    assert first == 1
    assert second == 2


def test_memory_resource_name_constant():
    from plugins.resources.memory_resource import MemoryResource

    assert MemoryResource.name == "memory"
    assert not hasattr(MemoryResource, "aliases")
