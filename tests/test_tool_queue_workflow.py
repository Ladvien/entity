import asyncio

from entity.core.resources.container import ResourceContainer
from pipeline.state import PipelineState
from pipeline import (
    PipelineStage,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
    PromptPlugin,
)


class EchoTool:
    async def execute_function(self, params):
        return params["text"]


class StageOne(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        await context.queue_tool_use("echo", result_key="greeting", text="hi")


class StageTwo(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    def __init__(self):
        super().__init__()
        self.loaded = None

    async def _execute_impl(self, context):
        self.loaded = context.load("greeting")
        context.set_response(self.loaded)


def test_tool_runs_before_next_stage():
    import pipeline.pipeline as pipeline_module

    pipeline_module.user_id = "test"

    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(StageOne(), PipelineStage.DO))
    stage_two = StageTwo()
    asyncio.run(plugins.register_plugin_for_stage(stage_two, PipelineStage.OUTPUT))

    tools = ToolRegistry()
    asyncio.run(tools.add("echo", EchoTool()))
    caps = SystemRegistries(ResourceContainer(), tools, plugins)

    state = PipelineState(conversation=[], pipeline_id="id")
    result = asyncio.run(execute_pipeline("start", caps, state=state))

    assert result == "hi"
    assert stage_two.loaded == "hi"
    assert state.stage_results["greeting"] == "hi"
