import asyncio

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
from pipeline.resources.memory import Memory


class ContinuePlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        if context.message == "start":
            context.set_response({"type": "continue_processing", "message": "next"})


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        if context.message == "next":
            context.set_response("done")


def make_manager():
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(ContinuePlugin({}), PipelineStage.DO))
    asyncio.run(plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.DO))
    resources = ResourceContainer()
    asyncio.run(resources.add("memory", Memory()))
    registries = SystemRegistries(resources, ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    memory = resources.get("memory")
    conv = memory.start_conversation(registries, manager)  # type: ignore[arg-type]
    return conv, manager


def test_conversation_manager_delegation():
    conv, manager = make_manager()

    async def run():
        result = await conv.process_request("start")
        return result

    result = asyncio.run(run())
    assert result == "done"
    assert not manager.has_active_pipelines()
