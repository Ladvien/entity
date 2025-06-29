import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginRegistry,
    ResourceRegistry,
    SimpleContext,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.plugins.tools.weather_api_tool import WeatherApiTool


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - test stub
        pass

    def json(self):
        return {"temp": "72F"}


async def run_weather():
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    tools = ToolRegistry()
    tool = WeatherApiTool({"base_url": "http://test/weather", "api_key": "key"})
    tools.add("weather", tool)
    registries = SystemRegistries(ResourceRegistry(), tools, PluginRegistry())
    ctx = SimpleContext(state, registries)
    with patch(
        "httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResponse())
    ) as mock_get:
        result = await ctx.use_tool("weather", location="Berlin")
        mock_get.assert_called_with(
            "http://test/weather",
            params={"location": "Berlin", "api_key": "key"},
        )
    return result


def test_weather_api_tool_returns_json():
    result = asyncio.run(run_weather())
    assert result == {"temp": "72F"}
