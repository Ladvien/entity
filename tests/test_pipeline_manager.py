import asyncio

from pipeline import (PipelineManager, PipelineStage, PluginRegistry,
                      PromptPlugin, ResourceRegistry, SystemRegistries,
                      ToolRegistry)


class WaitPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        await asyncio.sleep(0.05)
        context.set_response("ok")


def make_manager():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(WaitPlugin({}), PipelineStage.DO)
    regs = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
    return PipelineManager(regs)


def test_pipeline_manager_active_flag():
    manager = make_manager()

    async def run_task():
        task = manager.start_pipeline("hi")
        assert manager.has_active_pipelines()
        res = await task
        return res

    result = asyncio.run(run_task())
    assert result == "ok"
    assert not manager.has_active_pipelines()
