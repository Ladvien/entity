import asyncio
from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
from pipeline.tools.execution import execute_pending_tools
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
    registries = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    ctx = PluginContext(state, registries)
    key = ctx.execute_tool("search", {"query": "open source"})
    result = (await execute_pending_tools(state, registries))[key]
    return result


def test_search_tool_returns_result():
    result = asyncio.run(run_search())
    assert isinstance(result, str) and result
