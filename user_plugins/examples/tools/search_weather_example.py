"""Minimal example running SearchTool and WeatherApiTool."""

from __future__ import annotations

import asyncio
import os

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

from user_plugins.tools import SearchTool, WeatherApiTool


async def main() -> None:
    search_tool = SearchTool()
    weather_tool = WeatherApiTool({"api_key": os.environ.get("WEATHER_API_KEY", "")})
    search = await search_tool.execute_function({"query": "OpenAI news"})
    try:
        weather = await weather_tool.execute_function({"location": "Berlin"})
    except Exception as exc:  # pragma: no cover - network error
        weather = str(exc)
    print(f"{search} Weather: {weather}")


if __name__ == "__main__":
    asyncio.run(main())
