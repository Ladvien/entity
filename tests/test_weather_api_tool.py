import asyncio
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from config.environment import load_env
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
from pipeline.plugins.tools.weather_api_tool import WeatherApiTool

load_env(Path(__file__).resolve().parents[1] / ".env")


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
    tool = WeatherApiTool(
        {"base_url": "http://test/weather", "api_key": os.environ["WEATHER_API_KEY"]}
    )
    tools.add("weather", tool)
    registries = SystemRegistries(ResourceRegistry(), tools, PluginRegistry())
    ctx = PluginContext(state, registries)
    with patch(
        "httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResponse())
    ) as mock_get:
        key = ctx.execute_tool("weather", {"location": "Berlin"})
        result = (await execute_pending_tools(state, registries))[key]
        mock_get.assert_called_with(
            "http://test/weather",
            params={"location": "Berlin", "api_key": os.environ["WEATHER_API_KEY"]},
        )
    return result


def test_weather_api_tool_returns_json():
    result = asyncio.run(run_weather())
    assert result == {"temp": "72F"}
