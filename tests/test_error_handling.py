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
    PluginContextError,
    PluginExecutionError,
    ResourceError,
    StageExecutionError,
    ToolExecutionError,
    create_error_response,
    create_static_error_response,
)
from pipeline.resources import ResourceContainer
from pipeline.state import FailureInfo
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
    plugins.register_plugin_for_stage(main_plugin({}), PipelineStage.DO)
    plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR)
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


def test_create_error_response():
    info = FailureInfo(
        stage="do",
        plugin_name="Boom",
        error_type="RuntimeError",
        error_message="bad",
        original_exception=RuntimeError("bad"),
    )
    resp = create_error_response("id", info)
    assert resp["plugin"] == "Boom"
    assert resp["stage"] == "do"
    assert resp["type"] == "plugin_error"


def test_error_hierarchy():
    assert issubclass(PluginExecutionError, PipelineError)
    assert issubclass(ToolExecutionError, PipelineError)
    assert issubclass(ResourceError, PipelineError)


def test_resource_error_propagation():
    registries = make_registries(FallbackPlugin, main_plugin=ResourceFailPlugin)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == {"error": "missing resource"}


def test_contextual_errors():
    err = StageExecutionError(PipelineStage.DO, "boom", {"step": "run"})
    assert err.stage == PipelineStage.DO
    assert err.context["step"] == "run"

    perr = PluginContextError(PipelineStage.DO, "BoomPlugin", "crashed", {"id": 1})
    assert perr.stage == PipelineStage.DO
    assert perr.plugin_name == "BoomPlugin"
    assert perr.context["id"] == 1
