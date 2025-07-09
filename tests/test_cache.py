from datetime import datetime

import pipeline.context as context_module
from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineStage,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.base_plugins import PromptPlugin
from pipeline.cache import InMemoryCache
from pipeline.state import ToolCall
from pipeline.tools.execution import execute_pending_tools
from plugins.builtin.resources.llm_base import LLM

from entity.core.resources.container import ResourceContainer
from user_plugins.resources.cache import CacheResource

context_module.LLM = LLM


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, prompt: str) -> str:
        self.calls += 1
        return "pong"


class DummyPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        await self.call_llm(context, "hi", "test")


class FakeTool:
    def __init__(self) -> None:
        self.calls = 0

    async def execute_function(self, params):
        self.calls += 1
        return params["x"] * 2


async def make_context(cache: CacheResource, llm: FakeLLM):
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="123",
        metrics=MetricsCollector(),
        current_stage=PipelineStage.THINK,
    )
    resources = ResourceContainer()
    await resources.add("llm", llm)
    await resources.add("cache", cache)
    capabilities = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return PluginContext(state, capabilities), state, capabilities


async def test_llm_results_are_cached():
    llm = FakeLLM()
    cache = CacheResource(InMemoryCache())
    ctx, _, _ = await make_context(cache, llm)
    plugin = DummyPlugin({})

    await plugin.call_llm(ctx, "hello", "test")
    await plugin.call_llm(ctx, "hello", "test")

    assert llm.calls == 1


async def test_tool_results_are_cached():
    llm = FakeLLM()
    cache = CacheResource(InMemoryCache())
    ctx, state, capabilities = await make_context(cache, llm)

    tool = FakeTool()
    await capabilities.tools.add("fake", tool)

    await ctx.queue_tool_use("fake", result_key="r1", x=2)
    await execute_pending_tools(state, capabilities)

    await ctx.queue_tool_use("fake", result_key="r2", x=2)
    await execute_pending_tools(state, capabilities)

    assert tool.calls == 1
    assert ctx.load("r1") == ctx.load("r2")
