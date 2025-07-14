from __future__ import annotations

"""Simplistic server facade for built-in adapters."""

from typing import Any


from .cli import CLIAdapter
from .http_adapter import HTTPAdapter
from .websocket import WebSocketAdapter


class AgentServer:
    """Expose adapter-based serving helpers."""

    def __init__(self, *, capabilities: Any, manager: Any | None = None) -> None:
        self.capabilities = capabilities
        self.manager = manager

    async def serve_http(self, **config: Any) -> None:
        adapter = HTTPAdapter(self.manager, config)
        await adapter.serve(self.capabilities)

    async def serve_websocket(self, **config: Any) -> None:
        adapter = WebSocketAdapter(self.manager, config)
        await adapter.serve(self.capabilities)

    async def serve_cli(self, **config: Any) -> None:
        adapter = CLIAdapter(self.manager, config)
        await adapter.serve(self.capabilities)
