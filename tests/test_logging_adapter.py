import asyncio
import logging

from entity.core.resources.container import ResourceContainer
from entity.core.runtime import _AgentRuntime
from pipeline import (PipelineStage, PluginRegistry, PromptPlugin,
                      SystemRegistries, ToolRegistry, execute_pipeline)


class LoggingAdapter(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        logging.info("adapter", extra={"response": context.state.response})


class EchoPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        entry = context.get_conversation_history()[0]
        context.set_response({"echo": entry.content})


def make_runtime() -> _AgentRuntime:
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.DELIVER)
    )
    asyncio.run(
        plugins.register_plugin_for_stage(LoggingAdapter({}), PipelineStage.DELIVER)
    )
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return _AgentRuntime(capabilities)


def test_logging_adapter_logs_response(caplog):
    runtime = make_runtime()
    caplog.set_level(logging.INFO)
    asyncio.run(execute_pipeline("hello", runtime.capabilities))
    assert any(
        getattr(record, "response", {}).get("echo") == "hello"
        for record in caplog.records
    )
