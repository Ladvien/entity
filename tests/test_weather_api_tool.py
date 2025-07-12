import asyncio
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from entity.core.resources.container import ResourceContainer
from pipeline import (
    ConversationEntry,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from user_plugins.tools.weather_api_tool import WeatherApiTool


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # pragma: no cover - simple server
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"temp": "72F"}')


def run_server(server: HTTPServer) -> None:
    server.serve_forever()


async def run_weather() -> dict:
    server = HTTPServer(("localhost", 0), Handler)
    thread = Thread(target=run_server, args=(server,), daemon=True)
    thread.start()
    base_url = f"http://localhost:{server.server_port}"
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
    )
    tools = ToolRegistry()
    tool = WeatherApiTool({"base_url": base_url, "api_key": "x"})
    await tools.add("weather", tool)
    capabilities = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    ctx = PluginContext(state, capabilities)
    try:
        result = await ctx.tool_use("weather", location="Berlin")
    finally:
        server.shutdown()
        thread.join()
    return result


def test_weather_api_tool_returns_json():
    assert asyncio.run(run_weather()) == {"temp": "72F"}
