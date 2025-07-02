import asyncio

from pipeline import (LLMResponse, PipelineStage, PluginRegistry, PromptPlugin,
                      ResourceRegistry, SystemRegistries, ToolPlugin,
                      ToolRegistry, execute_pipeline)


class EchoLLM:
    async def generate(self, prompt: str):
        return LLMResponse(content=prompt)


class EchoTool(ToolPlugin):
    required_params = ["text"]

    async def execute_function(self, params):
        return params["text"]


class MetricsPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.execute_tool("echo", {"text": "hello"})
        await self.call_llm(context, "hi", "test")
        context.set_response("ok")


def make_registries():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(MetricsPlugin({}), PipelineStage.DO)
    resources = ResourceRegistry()
    resources.add("llm", EchoLLM())
    tools = ToolRegistry()
    tools.add("echo", EchoTool({}))
    return SystemRegistries(resources, tools, plugins)


def test_metrics_collected():
    registries = make_registries()

    response, metrics = asyncio.run(
        execute_pipeline("start", registries, return_metrics=True)
    )
    assert response == "ok"

    data = metrics.to_dict()
    stage = str(PipelineStage.DO)
    plugin_key = f"{stage}:{MetricsPlugin.__name__}"
    assert plugin_key in data["plugin_durations"]
    assert plugin_key in data["llm_durations"]
    assert data["tool_execution_count"][f"{stage}:echo"] == 1
    assert data["llm_call_count"][f"{stage}:{MetricsPlugin.__name__}:test"] == 1
    assert data["pipeline_durations"] and data["pipeline_durations"][0] > 0
