import asyncio

from pipeline import (
    FailurePlugin,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class FailPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        raise RuntimeError("boom")


class ErrorPlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        info = context._state.failure_info
        context.set_response({"error": info.error_message})


class BadErrorPlugin(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        raise RuntimeError("bad")


def make_registries(error_plugin):
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(FailPlugin({}), PipelineStage.DO)
    plugins.register_plugin_for_stage(error_plugin({}), PipelineStage.ERROR)
    return SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)


def test_error_stage_execution():
    regs = make_registries(ErrorPlugin)
    result = asyncio.run(execute_pipeline("hi", regs))
    assert result == {"error": "boom"}


def test_static_fallback_on_error_stage_failure():
    regs = make_registries(BadErrorPlugin)
    result = asyncio.run(execute_pipeline("hi", regs))
    assert result["type"] == "static_fallback"
