# isort: off
import asyncio
import logging

from pipeline import (
    FailurePlugin,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.resources import ResourceContainer
from user_plugins.failure.basic_logger import BasicLogger
from user_plugins.failure.error_formatter import ErrorFormatter

# isort: on


class FailPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise RuntimeError("boom")


class ErrorPlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        info = context.get_failure_info()
        assert info is not None
        context.set_response({"error": info.error_message})


class BadErrorPlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        raise RuntimeError("bad")


def make_registries(error_plugin):
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(FailPlugin({}), PipelineStage.DO))
    asyncio.run(plugins.register_plugin_for_stage(BasicLogger({}), PipelineStage.ERROR))
    asyncio.run(
        plugins.register_plugin_for_stage(error_plugin({}), PipelineStage.ERROR)
    )
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_error_stage_execution(caplog):
    """Verify error plugins run and log failures."""
    log_capture = caplog
    log_capture.set_level(logging.ERROR)
    registries = make_registries(ErrorPlugin)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == {"error": "boom"}
    assert any(
        record.message == "Pipeline failure encountered"
        and getattr(record, "pipeline_id", None)
        and getattr(record, "stage", None) == "do"
        for record in log_capture.records
    )


def test_static_fallback_on_error_stage_failure():
    registries = make_registries(BadErrorPlugin)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result.type == "static_fallback"


def test_error_formatter_produces_message():
    """Ensure ErrorFormatter creates a user-facing error message."""
    registries = make_registries(ErrorFormatter)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result["message"] == "FailPlugin failed (RuntimeError): boom"
    assert result["error"] == "boom"
    assert result["type"] == "formatted_error"
