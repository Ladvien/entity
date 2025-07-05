from __future__ import annotations

"""Adapter implementations used to expose the pipeline externally."""

from .cli import CLIAdapter
from .http import HTTPAdapter
from .websocket import WebSocketAdapter

try:  # optional gRPC adapter
    from .grpc import LLMGRPCAdapter
except ImportError:  # pragma: no cover - grpc optional
    LLMGRPCAdapter = None

__all__ = ["HTTPAdapter", "CLIAdapter", "WebSocketAdapter"]
if LLMGRPCAdapter is not None:
    __all__.append("LLMGRPCAdapter")
