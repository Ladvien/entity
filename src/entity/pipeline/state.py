from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from entity.core.state import ConversationEntry, FailureInfo, LLMResponse
from entity.core.state import PipelineState as CoreState
from entity.core.state import ToolCall

__all__ = [
    "ConversationEntry",
    "FailureInfo",
    "LLMResponse",
    "PipelineState",
    "ToolCall",
]


@dataclass
class PipelineState(CoreState):  # type: ignore[misc]
    """Extended state with failure tracking."""

    failure_info: Optional[FailureInfo] = None
