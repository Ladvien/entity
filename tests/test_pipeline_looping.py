import asyncio
from typing import Optional

from entity.core.resources.container import ResourceContainer
from entity.core.state import FailureInfo, PipelineState
from pipeline import (
    FailurePlugin,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class CountingDeliverPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config)
        self.calls = 0

    async def _execute_impl(self, context):
        self.calls += 1
        if self.calls == 2:
            context.set_response("ok")


class NoResponseDeliverPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config)
        self.calls = 0

    async def _execute_impl(self, context):
        self.calls += 1
        # never sets a response


class RecordFailurePlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    def __init__(self, store: list[FailureInfo]):
        super().__init__()
        self.store = store

    async def _execute_impl(self, context):
        info = context.failure_info
        if info:
            self.store.append(info)


async def make_capabilities(plugin):
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(plugin, PipelineStage.DELIVER)
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_pipeline_loops_until_response():
    plugin = CountingDeliverPlugin({})

    async def run():
        capabilities = await make_capabilities(plugin)
        result = await execute_pipeline("hi", capabilities)
        return result

    result = asyncio.run(run())
    assert result == "ok"
    assert plugin.calls == 2


def test_max_iterations_triggers_error():
    plugin = NoResponseDeliverPlugin({})
    failures: list[FailureInfo] = []

    async def run() -> PipelineState:
        plugins = PluginRegistry()
        await plugins.register_plugin_for_stage(plugin, PipelineStage.DELIVER)
        await plugins.register_plugin_for_stage(
            RecordFailurePlugin(failures), PipelineStage.ERROR
        )
        capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
        state = PipelineState(conversation=[], pipeline_id="id")
        result = await execute_pipeline(
            "hi", capabilities, state=state, max_iterations=2  # type: ignore[arg-type]
        )
        assert isinstance(result, dict)
        return state

    state = asyncio.run(run())
    assert state.iteration == 2
    assert failures
    assert failures[0].error_type == "max_iterations"
    assert failures[0].context_snapshot == state.to_dict()
