import asyncio
from datetime import datetime

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.context import ConversationEntry
from entity.core.resources.container import ResourceContainer
from pipeline.resources.memory import Memory
from plugins.builtin.resources.memory_storage import MemoryStorage


class IncrementPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]
    dependencies = ["memory"]

    async def _execute_impl(self, context):
        memory: Memory = context.get_resource("memory")
        count = memory.get("count", 0) + 1
        memory.set("count", count)
        context.set_response(count)


def make_registries():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(IncrementPlugin({}), PipelineStage.DELIVER)
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", Memory()))
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
        memory = Memory(config={})
        memory.database = storage
        history = [
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ]
        await memory.save_conversation("1", history)
        loaded = await memory.load_conversation("1")
        return loaded

    loaded = asyncio.run(run())
    assert loaded and loaded[0].content == "hi"


def test_memory_resource_name_constant():
    from pipeline.resources.memory import Memory

    assert Memory.name == "memory"
    assert not hasattr(Memory, "aliases")
