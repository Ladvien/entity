from __future__ import annotations

import asyncio
from entity.core.resources.container import ResourceContainer
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    PipelineWorker,
)
from entity.resources.memory import Memory


class CountingMemory(Memory):
    def __init__(self) -> None:
        super().__init__()
        self.load_calls = 0

    async def load_conversation(self, conversation_id: str):
        self.load_calls += 1
        return await super().load_conversation(conversation_id)


class EchoPlugin(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        context.set_response(context.conversation[-1].content)


async def make_registries(memory: Memory) -> SystemRegistries:
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.OUTPUT)
    resources = ResourceContainer()
    await resources.add("memory", memory)
    return SystemRegistries(resources, ToolRegistry(), plugins)


def test_worker_is_stateless_across_requests():
    async def run():
        memory = CountingMemory()
        regs = await make_registries(memory)
        worker = PipelineWorker(regs)
        pipeline_id = "pid"
        await memory.save_conversation(pipeline_id, [])
        await worker.execute_pipeline(pipeline_id, "hello")
        first_history = await memory.load_conversation(pipeline_id)
        await worker.execute_pipeline(pipeline_id, "again")
        second_history = await memory.load_conversation(pipeline_id)
        return first_history, second_history, memory.load_calls

    history1, history2, loads = asyncio.run(run())
    assert [e.content for e in history1] == ["hello"]
    assert [e.content for e in history2] == ["hello", "again"]
    assert loads >= 2
