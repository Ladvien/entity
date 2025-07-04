import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.pipeline import execute_pending_tools
from user_plugins.tools.search_tool import SearchTool


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return {"RelatedTopics": [{"Text": "Example Result"}]}


async def run_search():
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    tools = ToolRegistry()
    tools.add("search", SearchTool())
    registries = SystemRegistries(ResourceRegistry(), tools, PluginRegistry())
    ctx = PluginContext(state, registries)
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResponse())):
        key = ctx.execute_tool("search", {"query": "test"})
        result = (await execute_pending_tools(state, registries))[key]
    return result


def test_search_tool_registered_and_returns_result():
    result = asyncio.run(run_search())
    assert result == "Example Result"
