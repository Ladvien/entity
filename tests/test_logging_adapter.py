import asyncio
import logging

from plugins.builtin.adapters.logging_adapter import LoggingAdapter

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class DummyPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_response("ok")


def make_registries():
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(DummyPlugin({}), PipelineStage.DO))
    asyncio.run(
        plugins.register_plugin_for_stage(LoggingAdapter({}), PipelineStage.DELIVER)
    )
    return SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)


def test_logging_adapter_logs(caplog):
    registries = make_registries()
    caplog.set_level(logging.INFO)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == "ok"
    assert any(
        rec.message == "Pipeline response" and rec.levelno == logging.INFO
        for rec in caplog.records
    )
