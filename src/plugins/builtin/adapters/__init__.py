from __future__ import annotations

"""Adapter implementations used to expose the pipeline externally."""

from .cli import CLIAdapter
from .grpc import LLMGRPCAdapter
from .http import HTTPAdapter
from .logging import LoggingAdapter
<<<<<< codex/refactor-test-modules-and-improve-fixtures
from .logging_adapter import LoggingAdapter as FileLoggingAdapter
======
from .logging_adapter import LoggingAdapter as LoggingAdapterWrapper
>>>>>> main
from .websocket import WebSocketAdapter

__all__ = [
    "HTTPAdapter",
    "CLIAdapter",
    "WebSocketAdapter",
    "LLMGRPCAdapter",
    "LoggingAdapter",
<<<<<< codex/refactor-test-modules-and-improve-fixtures
    "FileLoggingAdapter",
======
    "LoggingAdapterWrapper",
>>>>>> main
]
