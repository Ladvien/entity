import asyncio
import logging

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from plugins.builtin.adapters.logging import LoggingAdapter

from entity.core.resources.container import ResourceContainer


class EchoPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        entry = context.get_conversation_history()[0]
        context.set_response({"echo": entry.content})


def make_manager() -> PipelineManager:
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.DELIVER)
    )
    asyncio.run(
        plugins.register_plugin_for_stage(LoggingAdapter({}), PipelineStage.DELIVER)
    )
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return PipelineManager(capabilities)


def test_logging_adapter_logs_response(caplog):
    manager = make_manager()
    caplog.set_level(logging.INFO)
    asyncio.run(manager.run_pipeline("hello"))
    assert any(
        getattr(record, "response", {}).get("echo") == "hello"
        for record in caplog.records
    )
