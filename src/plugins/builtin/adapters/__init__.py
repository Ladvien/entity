from __future__ import annotations

"""Adapter implementations used to expose the pipeline externally."""

from .cli import CLIAdapter
from .dashboard import DashboardAdapter

try:  # pragma: no cover - covered in tests
    from .grpc import LLMGRPCAdapter
except ImportError:  # pragma: no cover - absence of grpc is tested
    LLMGRPCAdapter = None  # type: ignore[assignment]

from .http import HTTPAdapter
from .logging import LoggingAdapter
from .logging_adapter import StructuredLoggingAdapter
from .websocket import WebSocketAdapter

__all__ = [
    "HTTPAdapter",
    "DashboardAdapter",
    "CLIAdapter",
    "WebSocketAdapter",
    "LoggingAdapter",
    "StructuredLoggingAdapter",
]

if LLMGRPCAdapter is not None:
    __all__.append("LLMGRPCAdapter")
