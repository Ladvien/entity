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
    temporary_thoughts: Dict[str, Any] = field(default_factory=dict)
    max_stage_results: int | None = 100
    pending_tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    pipeline_id: str = ""
    iteration: int = 0
    current_stage: Optional[PipelineStage] = None
    last_completed_stage: Optional[PipelineStage] = None
    next_stage: Optional[PipelineStage] = None
    skip_stages: set[PipelineStage] = field(default_factory=set)
    failure_info: "FailureInfo" | None = None

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
            "temporary_thoughts": self.temporary_thoughts,
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
            "next_stage": str(self.next_stage) if self.next_stage else None,
            "skip_stages": [str(s) for s in self.skip_stages],
            "max_stage_results": self.max_stage_results,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        conversation = [
            ConversationEntry(
                content=e["content"],
                role=e["role"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                metadata=e.get("metadata", {}),
            )
            for e in data.get("conversation", [])
        ]

        state = cls(conversation=conversation)
        state.response = data.get("response")
        state.prompt = data.get("prompt", "")
        state.stage_results = data.get("stage_results", {})
        state.temporary_thoughts = data.get("temporary_thoughts", {})
        state.pending_tool_calls = [
            ToolCall(
                name=c["name"],
                params=c.get("params", {}),
                result_key=c.get("result_key", ""),
                source=c.get("source", "direct_execution"),
            )
            for c in data.get("pending_tool_calls", [])
        ]
        state.metadata = data.get("metadata", {})
        state.pipeline_id = data.get("pipeline_id", "")
        state.iteration = data.get("iteration", 0)
        current = data.get("current_stage")
        state.current_stage = PipelineStage.from_str(current) if current else None
        last = data.get("last_completed_stage")
        state.last_completed_stage = PipelineStage.from_str(last) if last else None
        nxt = data.get("next_stage")
        state.next_stage = PipelineStage.from_str(nxt) if nxt else None
        skips = data.get("skip_stages", [])
        state.skip_stages = {PipelineStage.from_str(s) for s in skips}
        state.max_stage_results = data.get("max_stage_results")
        return state

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def _last_entry(self, role: str) -> Optional[ConversationEntry]:
        for entry in reversed(self.conversation):
            if entry.role == role:
                return entry
        return None

    def last_user_message(self) -> Optional[str]:
        entry = self._last_entry("user")
        return entry.content if entry else None

    def last_assistant_message(self) -> Optional[str]:
        entry = self._last_entry("assistant")
        return entry.content if entry else None

    def get_stage_result(self, key: str, default: Any | None = None) -> Any:
        return self.stage_results.get(key, default)

    def get_temp_thought(self, key: str, default: Any | None = None) -> Any:
        return self.temporary_thoughts.get(key, default)

    def clear_temp_thoughts(self) -> None:
        self.temporary_thoughts.clear()


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
