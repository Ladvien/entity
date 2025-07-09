import asyncio
from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineStage,
    PipelineState,
    PluginContext,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from entity.core.resources.container import ResourceContainer
from plugins.builtin.resources.echo_llm import EchoLLMResource


class DummyPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:  # pragma: no cover
        pass


def make_context(llm) -> PluginContext:
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="123",
        metrics=MetricsCollector(),
        current_stage=PipelineStage.THINK,
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("llm", llm))
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return PluginContext(state, registries)


def test_call_llm_logs_info(monkeypatch):
    llm = EchoLLMResource()
    ctx = make_context(llm)
    plugin = DummyPlugin({})

    recorded: dict[str, object] = {}

    def fake_info(message: str, *, extra=None, **kwargs):
        recorded["message"] = message
        if extra:
            recorded.update(extra)

    monkeypatch.setattr(plugin.logger, "info", fake_info)

    result = asyncio.run(plugin.call_llm(ctx, "hello", "test"))

    assert result.content == "hello"
    assert recorded["message"] == "LLM call completed"
    assert recorded["plugin"] == "DummyPlugin"
    assert recorded["stage"] == str(PipelineStage.THINK)
    assert recorded["purpose"] == "test"
    assert recorded["prompt_length"] == len("hello")
    assert recorded["response_length"] == len("hello")
    assert recorded["pipeline_id"] == "123"
    assert isinstance(recorded["duration"], float)
