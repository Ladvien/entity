"""Minimal pipeline using SearchTool and WeatherApiTool.

Run with ``python -m examples.tools.search_weather_example`` or install the
package in editable mode.
"""

from __future__ import annotations

import asyncio
import os


from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

from entity_config.environment import load_env
from pipeline import Agent
from pipeline.context import PluginContext
from user_plugins.tools import SearchTool, WeatherApiTool

load_env()

agent = Agent()
agent.tool_registry.add("search", SearchTool())
agent.tool_registry.add(
    "weather",
    WeatherApiTool({"api_key": os.environ.get("WEATHER_API_KEY", "")}),
)


@agent.plugin
async def gather(ctx: PluginContext) -> str:
    """Run both tools and combine their output."""
    search = await ctx.use_tool("search", query="OpenAI news")
    weather = await ctx.use_tool("weather", location="Berlin")
    return f"{search} Weather: {weather}"


async def main() -> None:
    result = await agent.handle("check tools")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
