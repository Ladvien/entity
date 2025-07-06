import asyncio
from datetime import datetime

from plugins.builtin.resources.memory_storage import MemoryStorage

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.context import ConversationEntry
from pipeline.resources import ResourceContainer
from pipeline.resources.memory import Memory
from pipeline.resources.memory_resource import MemoryResource, SimpleMemoryResource


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
    asyncio.run(
        plugins.register_plugin_for_stage(IncrementPlugin({}), PipelineStage.DO)
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", SimpleMemoryResource()))
    return SystemRegistries(resources, ToolRegistry(), plugins)


def test_memory_persists_between_runs():
    registries = make_registries()
    first = asyncio.run(execute_pipeline("hi", registries))
    second = asyncio.run(execute_pipeline("again", registries))
    assert first == 1
    assert second == 2


def test_save_and_load_history():
    async def run():
        storage = MemoryStorage({})
        memory = MemoryResource(storage=storage)
        history = [
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ]
        await memory.save_conversation("1", history)
        loaded = await memory.load_conversation("1")
        return loaded

    loaded = asyncio.run(run())
    assert loaded and loaded[0].content == "hi"


def test_memory_resource_name_constant():
    from plugins.builtin.resources.memory_resource import MemoryResource

    assert MemoryResource.name == "memory"
    assert not hasattr(MemoryResource, "aliases")
