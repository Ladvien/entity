from __future__ import annotations

"""Lightweight pipeline state objects."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .stages import PipelineStage


@dataclass
class ConversationEntry:
    content: str
    role: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    name: str
    params: Dict[str, Any]
    result_key: str
    source: str = "direct_execution"


@dataclass
class PipelineState:
    conversation: List[ConversationEntry]
    response: Any = None
    prompt: str = ""
    stage_results: Dict[str, Any] = field(default_factory=dict)
    max_stage_results: int | None = 100
    pending_tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    pipeline_id: str = ""
    iteration: int = 0
    current_stage: Optional[PipelineStage] = None
    last_completed_stage: Optional[PipelineStage] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation": [
                {
                    "content": e.content,
                    "role": e.role,
                    "timestamp": e.timestamp.isoformat(),
                    "metadata": e.metadata,
                }
                for e in self.conversation
            ],
            "response": self.response,
            "prompt": self.prompt,
            "stage_results": self.stage_results,
            "pending_tool_calls": [
                {
                    "name": c.name,
                    "params": c.params,
                    "result_key": c.result_key,
                    "source": c.source,
                }
                for c in self.pending_tool_calls
            ],
            "metadata": self.metadata,
            "pipeline_id": self.pipeline_id,
            "iteration": self.iteration,
            "current_stage": str(self.current_stage) if self.current_stage else None,
            "last_completed_stage": (
                str(self.last_completed_stage) if self.last_completed_stage else None
            ),
            "max_stage_results": self.max_stage_results,
        }


@dataclass
class FailureInfo:
    stage: str
    plugin_name: str
    error_type: str
    error_message: str
    original_exception: Exception | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    context_snapshot: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    content: str
