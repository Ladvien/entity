import asyncio

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.resources import ResourceContainer


class FlakyPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    def __init__(self, config=None):
        super().__init__(config)
        self.calls = 0

    async def _execute_impl(self, context):
        self.calls += 1
        if self.calls < 2:
            raise RuntimeError("boom")
        context.set_response("ok")


def test_plugin_retry_succeeds():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(
            FlakyPlugin({"retry_attempts": 2, "retry_backoff": 0}),
            PipelineStage.DO,
        )
    )
    regs = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    result = asyncio.run(execute_pipeline("hi", regs))
    assert result == "ok"
