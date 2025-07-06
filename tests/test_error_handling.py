import asyncio

from pipeline import (
    FailurePlugin,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.errors import (
    PipelineError,
    PluginExecutionError,
    ResourceError,
    ToolExecutionError,
    create_static_error_response,
)
from pipeline.resources import ResourceContainer
from user_plugins.failure.basic_logger import BasicLogger


class BoomPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise PluginExecutionError("BoomPlugin", RuntimeError("boom"))


class ResourceFailPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise ResourceError("missing resource")


class FallbackPlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        info = context.get_failure_info()
        context.set_response({"error": info.error_message})


def make_registries(error_plugin, main_plugin=BoomPlugin):
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(main_plugin({}), PipelineStage.DO))
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    asyncio.run(
        plugins.register_plugin_for_stage(error_plugin({}), PipelineStage.ERROR)
    )
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_error_plugin_runs():
    registries = make_registries(FallbackPlugin)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == {"error": "boom"}


def test_static_error_response():
    pipeline_id = "123"
    resp = create_static_error_response(pipeline_id)
    assert resp["error_id"] == pipeline_id
    assert resp["type"] == "static_fallback"


def test_error_hierarchy():
    assert issubclass(PluginExecutionError, PipelineError)
    assert issubclass(ToolExecutionError, PipelineError)
    assert issubclass(ResourceError, PipelineError)


def test_resource_error_propagation():
    registries = make_registries(FallbackPlugin, main_plugin=ResourceFailPlugin)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == {"error": "missing resource"}
