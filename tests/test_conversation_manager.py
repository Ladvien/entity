import asyncio

from pipeline import (ConversationManager, PipelineManager, PipelineStage,
                      PluginRegistry, PromptPlugin, ResourceRegistry,
                      SystemRegistries, ToolRegistry)


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
    plugins.register_plugin_for_stage(ContinuePlugin({}), PipelineStage.DO)
    plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    conv = ConversationManager(registries, manager)
    return conv, manager


def test_conversation_manager_delegation():
    conv, manager = make_manager()

    async def run():
        result = await conv.process_request("start")
        return result

    result = asyncio.run(run())
    assert result == "done"
    assert not manager.has_active_pipelines()
