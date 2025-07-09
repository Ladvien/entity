import asyncio

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources.memory import Memory

from entity.core.resources.container import ResourceContainer


class ContinuePlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        if context.message == "start":
            context.set_response({"type": "continue_processing", "message": "next"})


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        if context.message == "next":
            context.set_response("done")


def make_manager():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(ContinuePlugin({}), PipelineStage.DELIVER)
    )
    asyncio.run(
        plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.DELIVER)
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", Memory()))
    capabilities = SystemRegistries(resources, ToolRegistry(), plugins)
    manager = PipelineManager(capabilities)
    memory = resources.get("memory")
    conv = memory.start_conversation(capabilities, manager)  # type: ignore[arg-type]
    return conv, manager


def test_conversation_manager_delegation():
    conv, manager = make_manager()

    async def run():
        result = await conv.process_request("start")
        return result

    result = asyncio.run(run())
    assert result == "done"
    assert not manager.has_active_pipelines()
