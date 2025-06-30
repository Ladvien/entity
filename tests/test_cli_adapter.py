import asyncio
from typing import Any

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.adapters.cli import CLIAdapter


class EchoPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_response({"msg": context._state.conversation[0].content})


def make_adapter() -> tuple[CLIAdapter, SystemRegistries]:
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    return CLIAdapter(manager), registries


def test_cli_adapter_round_trip(monkeypatch):
    adapter, registries = make_adapter()
    inputs: list[Any] = ["hello", EOFError()]
    outputs: list[str] = []

    def fake_input(prompt: str = "") -> str:
        value = inputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return str(value)

    def fake_print(*args, **kwargs) -> None:
        outputs.append(" ".join(str(a) for a in args))

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", fake_print)

    asyncio.run(adapter.serve(registries))
    combined = " ".join(outputs)
    assert "'msg': 'hello'" in combined
