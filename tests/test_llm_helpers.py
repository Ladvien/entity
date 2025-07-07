import asyncio
from datetime import datetime

import pytest

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
from pipeline.errors import ResourceError
from pipeline.resources import ResourceContainer


class StubLLM:
    async def generate(self, prompt: str) -> str:
        return prompt


def make_context(llm=None) -> PluginContext:
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceContainer()
    if llm is not None:
        asyncio.run(resources.add("llm", llm))
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return PluginContext(state, registries)


def test_ask_llm_returns_text():
    ctx = make_context(StubLLM())
    result = asyncio.run(ctx.ask_llm("hello"))
    assert result == "hello"


def test_ask_llm_without_llm_resource_raises():
    ctx = make_context()
    with pytest.raises(ResourceError):
        asyncio.run(ctx.ask_llm("hi"))


class DummyPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(
        self, context: PluginContext
    ) -> None:  # pragma: no cover - not used
        pass


def test_base_plugin_call_llm():
    ctx = make_context(StubLLM())
    plugin = DummyPlugin({})
    response = asyncio.run(plugin.call_llm(ctx, "test", "testing"))
    assert response.content == "test"


def test_ask_llm_uses_running_loop(monkeypatch):
    ctx = make_context(StubLLM())

    class DummyLoop:
        def time(self) -> float:  # pragma: no cover - helper
            called["time"] = True
            return 0.0

    called: dict[str, bool] = {}

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: DummyLoop())
    monkeypatch.setattr(
        asyncio,
        "get_event_loop",
        lambda: (_ for _ in ()).throw(AssertionError("deprecated")),
    )

    result = asyncio.run(ctx.ask_llm("hello"))
    assert result == "hello"
    assert called.get("time") is True
