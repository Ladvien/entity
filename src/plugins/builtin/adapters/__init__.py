"""Built-in adapter stubs."""

from .http_adapter import HTTPAdapter
from .cli import CLIAdapter
from .websocket import WebSocketAdapter
from .dashboard import DashboardAdapter
from .server import AgentServer

__all__ = [
    "HTTPAdapter",
    "CLIAdapter",
    "WebSocketAdapter",
    "DashboardAdapter",
    "AgentServer",
]
