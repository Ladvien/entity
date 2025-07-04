from __future__ import annotations

import asyncio

from pipeline.runtime import AgentRuntime
from plugins.adapters.http import HTTPAdapter
from plugins.adapters.websocket import WebSocketAdapter


class AgentServer:
    """Run HTTP or WebSocket servers for an agent."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime

    def create_http_adapter(
        self, host: str = "127.0.0.1", port: int = 8000
    ) -> HTTPAdapter:
        cfg = {"host": host, "port": port}
        return HTTPAdapter(manager=self.runtime.manager, config=cfg)

    def create_websocket_adapter(
        self, host: str = "127.0.0.1", port: int = 8001
    ) -> WebSocketAdapter:
        cfg = {"host": host, "port": port}
        return WebSocketAdapter(manager=self.runtime.manager, config=cfg)

    async def serve_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        adapter = self.create_http_adapter(host, port)
        await adapter.serve(self.runtime.registries)

    async def serve_websocket(self, host: str = "127.0.0.1", port: int = 8001) -> None:
        adapter = self.create_websocket_adapter(host, port)
        await adapter.serve(self.runtime.registries)

    def run_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        asyncio.run(self.serve_http(host, port))

    def run_websocket(self, host: str = "127.0.0.1", port: int = 8001) -> None:
        asyncio.run(self.serve_websocket(host, port))
