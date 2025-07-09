import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from entity.core.resources.container import ResourceContainer
from user_plugins.failure.basic_logger import BasicLogger


class FlakyPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    def __init__(self, config=None):
        super().__init__(config)
        self.calls = 0

    async def _execute_impl(self, context):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        context.set_response("ok")


def make_registries():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(
            FlakyPlugin({"max_retries": 1, "retry_delay": 0}), PipelineStage.DELIVER
        )
    )
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_plugin_retry_succeeds():
    registries = make_registries()
    plugin = registries.plugins.get_plugins_for_stage(PipelineStage.DO)[0]
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == "ok"
    assert plugin.calls == 2
