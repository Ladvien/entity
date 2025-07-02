import asyncio

from pipeline import (FailurePlugin, PipelineStage, PluginRegistry,
                      PromptPlugin, ResourceRegistry, SystemRegistries,
                      ToolRegistry, execute_pipeline)
from pipeline.errors import create_static_error_response
from pipeline.plugins.failure.basic_logger import BasicLogger


class BoomPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise RuntimeError("boom")


class FallbackPlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        info = context.get_failure_info()
        context.set_response({"error": info.error_message})


def make_registries(error_plugin):
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(BoomPlugin({}), PipelineStage.DO)
    plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR)
    plugins.register_plugin_for_stage(error_plugin({}), PipelineStage.ERROR)
    return SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)


def test_error_plugin_runs():
    registries = make_registries(FallbackPlugin)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == {"error": "boom"}


def test_static_error_response():
    pipeline_id = "123"
    resp = create_static_error_response(pipeline_id)
    assert resp["error_id"] == pipeline_id
    assert resp["type"] == "static_fallback"
