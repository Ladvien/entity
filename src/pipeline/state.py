from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .metrics import MetricsCollector
from .stages import PipelineStage


@dataclass
class LLMResponse:
    """Result returned by an LLM call."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost: float | None = None


@dataclass
class ConversationEntry:
    """Single message stored in the conversation history.

    Attributes:
        content: Message text.
        role: Speaker role (e.g. ``user`` or ``assistant``).
        timestamp: When the message was created.
        metadata: Extra data recorded with the entry.
    """

    content: str
    role: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(eq=False)
class ToolCall:
    """Description of a tool execution request.

    Attributes:
        name: Registry key of the tool to run.
        params: Parameters passed to the tool.
        result_key: Key used to store the tool result.
        source: Origin of the call (direct or generated).
    """

    name: str
    params: Dict[str, Any]
    result_key: str
    source: str = "direct_execution"


@dataclass
class FailureInfo:
    """Captured information about a pipeline failure.

    Attributes:
        stage: Stage in which the error occurred.
        plugin_name: Plugin reporting the failure.
        error_type: Name of the raised exception class.
        error_message: Human readable description.
        original_exception: Original exception instance.
        context_snapshot: Optional snapshot of pipeline state.
        timestamp: When the failure was recorded.
    """

    stage: str
    plugin_name: str
    error_type: str
    error_message: str
    original_exception: Exception
    context_snapshot: Dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PipelineState:
    """Mutable state shared across pipeline stages.

    This object is created at the start of each pipeline run and is
    passed to every plugin.

    Attributes:
        conversation: History of conversation messages.
        response: Final response to return to the caller.
        prompt: Prompt text currently being processed.
        stage_results: Values produced during stage execution.
        pending_tool_calls: Tool calls awaiting execution.
        metadata: Arbitrary per-run metadata for user_plugins.
        pipeline_id: Unique identifier for this run.
        current_stage: Stage that is currently executing.
        metrics: Collector used to record runtime metrics.
        failure_info: Details about any failure encountered.
    """

    conversation: List[ConversationEntry]
    response: Any = None
    prompt: str = ""
    stage_results: Dict[str, Any] = field(default_factory=dict)
    max_stage_results: int | None = 100
    pending_tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    pipeline_id: str = ""
    current_stage: Optional[PipelineStage] = None
    last_completed_stage: Optional[PipelineStage] = None
    metrics: MetricsCollector = field(default_factory=MetricsCollector)
    failure_info: Optional[FailureInfo] = None

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
            "current_stage": str(self.current_stage) if self.current_stage else None,
            "last_completed_stage": (
                str(self.last_completed_stage) if self.last_completed_stage else None
            ),
            "max_stage_results": self.max_stage_results,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        state = cls(
            conversation=[
                ConversationEntry(
                    content=e["content"],
                    role=e["role"],
                    timestamp=datetime.fromisoformat(e["timestamp"]),
                    metadata=e.get("metadata", {}),
                )
                for e in data.get("conversation", [])
            ],
            response=data.get("response"),
            prompt=data.get("prompt", ""),
            stage_results=data.get("stage_results", {}),
            pending_tool_calls=[
                ToolCall(
                    name=c["name"],
                    params=c.get("params", {}),
                    result_key=c["result_key"],
                    source=c.get("source", "direct_execution"),
                )
                for c in data.get("pending_tool_calls", [])
            ],
            metadata=data.get("metadata", {}),
            pipeline_id=data.get("pipeline_id", ""),
            current_stage=(
                PipelineStage.from_str(data["current_stage"])
                if data.get("current_stage")
                else None
            ),
            last_completed_stage=(
                PipelineStage.from_str(data["last_completed_stage"])
                if data.get("last_completed_stage")
                else None
            ),
            max_stage_results=data.get("max_stage_results", 100),
        )
        return state
