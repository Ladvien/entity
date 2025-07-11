from __future__ import annotations

"""Simplistic server facade for built-in adapters."""

from typing import Any

from entity.core.runtime import AgentRuntime

from .cli import CLIAdapter
from .http_adapter import HTTPAdapter
from .websocket import WebSocketAdapter


class AgentServer:
    """Expose adapter-based serving helpers."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime

    async def serve_http(self, **config: Any) -> None:
        adapter = HTTPAdapter(self.runtime.manager, config)
        await adapter.serve(self.runtime.capabilities)

    async def serve_websocket(self, **config: Any) -> None:
        adapter = WebSocketAdapter(self.runtime.manager, config)
        await adapter.serve(self.runtime.capabilities)

    async def serve_cli(self, **config: Any) -> None:
        adapter = CLIAdapter(self.runtime.manager, config)
        await adapter.serve(self.runtime.capabilities)
