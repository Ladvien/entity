import asyncio
import logging
from typing import Any

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from plugins.builtin.adapters.cli import CLIAdapter

from entity.core.resources.container import ResourceContainer


class EchoPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        first = context.get_conversation_history()[0]
        context.set_response({"msg": first.content})


def make_adapter() -> tuple[CLIAdapter, SystemRegistries]:
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.DELIVER)
    )
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    manager = PipelineManager(capabilities)
    return CLIAdapter(manager), capabilities


def test_cli_adapter_round_trip(monkeypatch, caplog):
    adapter, capabilities = make_adapter()
    inputs: list[Any] = ["hello", EOFError()]

    def fake_input(prompt: str = "") -> str:
        value = inputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return str(value)

    monkeypatch.setattr("builtins.input", fake_input)

    caplog.set_level(logging.INFO)
    asyncio.run(adapter.serve(capabilities))
    assert any("'msg': 'hello'" in record.getMessage() for record in caplog.records)
