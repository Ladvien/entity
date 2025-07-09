import asyncio
from datetime import datetime

from entity.core.resources.container import ResourceContainer
from entity.core.state import MetricsCollector
from pipeline import (
    ConversationEntry,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from user_plugins.tools.search_tool import SearchTool


async def run_search() -> str:
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    tools = ToolRegistry()
    await tools.add("search", SearchTool())
    capabilities = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    ctx = PluginContext(state, capabilities)
    return await ctx.tool_use("search", query="open source")


def test_search_tool_returns_result():
    result = asyncio.run(run_search())
    assert isinstance(result, str) and result
