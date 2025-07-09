from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from entity.core.state import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    ToolCall,
)


@dataclass
class FailureInfo:
    stage: str
    plugin_name: str
    error_type: str
    error_message: str
    original_exception: Exception | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LLMResponse:
    content: str


__all__ = [
    "ConversationEntry",
    "ToolCall",
    "MetricsCollector",
    "PipelineState",
    "FailureInfo",
    "LLMResponse",
]
