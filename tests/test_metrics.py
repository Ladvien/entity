import asyncio

from pipeline import (
    LLMResponse,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)

from entity.core.resources.container import ResourceContainer


class EchoLLM:
    async def generate(self, prompt: str):
        return LLMResponse(content=prompt)


class EchoTool(ToolPlugin):
    required_params = ["text"]

    async def execute_function(self, params):
        return params["text"]


class MetricsPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        await context.tool_use("echo", text="hello")
        await self.call_llm(context, "hi", "test")
        context.set_response("ok")


def make_capabilities():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(MetricsPlugin({}), PipelineStage.DELIVER)
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("llm", EchoLLM()))
    tools = ToolRegistry()
    asyncio.run(tools.add("echo", EchoTool({})))
    return SystemRegistries(resources, tools, plugins)


def test_metrics_collected():
    capabilities = make_capabilities()

    response, metrics = asyncio.run(
        execute_pipeline("start", capabilities, return_metrics=True)
    )
    assert response == "ok"

    data = metrics.to_dict()
    stage = str(PipelineStage.DELIVER)
    plugin_key = f"{stage}:{MetricsPlugin.__name__}"
    assert plugin_key in data["plugin_durations"]
    assert plugin_key in data["llm_durations"]
    assert data["tool_execution_count"][f"{stage}:echo"] == 1
    assert data["llm_call_count"][f"{stage}:{MetricsPlugin.__name__}:test"] == 1
    assert data["pipeline_durations"] and data["pipeline_durations"][0] > 0
    assert stage in data["stage_durations"]
