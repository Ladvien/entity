import asyncio
from datetime import datetime

from entity.core.resources.container import ResourceContainer
from entity.core.state import ConversationEntry
from entity.resources.memory import Memory
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class IncrementPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]
    dependencies = ["memory"]

    async def _execute_impl(self, context):
        memory: Memory = context.get_resource("memory")
        count = memory.get("count", 0) + 1
        memory.remember("count", count)
        context.set_response(count)


def make_capabilities():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(IncrementPlugin({}), PipelineStage.DELIVER)
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", Memory()))
    return SystemRegistries(resources, ToolRegistry(), plugins)


def test_memory_persists_between_runs():
    capabilities = make_capabilities()
    first = asyncio.run(execute_pipeline("hi", capabilities))
    second = asyncio.run(execute_pipeline("again", capabilities))
    assert first == 1
    assert second == 2


def test_save_and_load_history():
    async def run():
        memory = Memory(config={})
        history = [
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ]
        await memory.save_conversation("1", history)
        loaded = await memory.load_conversation("1")
        return loaded

    loaded = asyncio.run(run())
    assert loaded and loaded[0].content == "hi"


def test_memory_resource_name_constant():
    from entity.resources.memory import Memory

    assert Memory.name == "memory"
    assert not hasattr(Memory, "aliases")
