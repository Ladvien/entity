import asyncio

from entity.core.resources.container import ResourceContainer
from entity.resources.memory import Memory
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)


class ContinuePlugin(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        if context.message == "start":
            context.set_response({"type": "continue_processing", "message": "next"})


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        if context.message == "next":
            context.set_response("done")


def make_conversation():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(ContinuePlugin({}), PipelineStage.OUTPUT)
    )
    asyncio.run(
        plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.OUTPUT)
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", Memory()))
    capabilities = SystemRegistries(resources, ToolRegistry(), plugins)
    memory = resources.get("memory")
    conv = memory.start_conversation(capabilities)
    return conv


def test_conversation_manager_delegation():
    conv = make_conversation()

    async def run():
        result = await conv.process_request("start")
        return result

    result = asyncio.run(run())
    assert result == "done"
