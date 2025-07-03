import asyncio
from datetime import datetime

import pytest

from pipeline import (ConversationEntry, MetricsCollector, PipelineStage,
                      PipelineState, PluginContext, PluginRegistry,
                      PromptPlugin, ResourceRegistry, SystemRegistries,
                      ToolRegistry)


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
    resources = ResourceRegistry()
    if llm is not None:
        resources.add("llm", llm)
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return PluginContext(state, registries)


def test_ask_llm_returns_text():
    ctx = make_context(StubLLM())
    result = asyncio.run(ctx.ask_llm("hello"))
    assert result == "hello"


def test_ask_llm_without_llm_resource_raises():
    ctx = make_context()
    with pytest.raises(RuntimeError):
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
