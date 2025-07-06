import asyncio
import logging

from plugins.builtin.adapters.logging import LoggingAdapter

<<<<<<< HEAD
from pipeline import (PipelineManager, PipelineStage, PluginRegistry,
                      PromptPlugin, ResourceContainer, SystemRegistries,
                      ToolRegistry)
=======
from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
>>>>>>> 842b365f2ee0307cf77e24d7bdb710602bc576a8


class EchoPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        entry = context.get_conversation_history()[0]
        context.set_response({"echo": entry.content})


def make_manager() -> PipelineManager:
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.DO))
    asyncio.run(
        plugins.register_plugin_for_stage(LoggingAdapter({}), PipelineStage.DELIVER)
    )
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return PipelineManager(registries)


def test_logging_adapter_logs_response(caplog):
    manager = make_manager()
    caplog.set_level(logging.INFO)
    asyncio.run(manager.run_pipeline("hello"))
    assert any(
        getattr(record, "response", {}).get("echo") == "hello"
        for record in caplog.records
    )
