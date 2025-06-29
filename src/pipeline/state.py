from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .stages import PipelineStage


@dataclass
class LLMResponse:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationEntry:
    content: str
    role: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(eq=False)
class ToolCall:
    name: str
    params: Dict[str, Any]
    result_key: str
    source: str = "direct_execution"


@dataclass
class FailureInfo:
    stage: str
    plugin_name: str
    error_type: str
    error_message: str
    original_exception: Exception
    context_snapshot: Dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MetricsCollector:
    """Collect simple pipeline metrics."""

    pipeline_durations: list[float] = field(default_factory=list)
    plugin_durations: dict[str, list[float]] = field(default_factory=dict)
    tool_execution_count: dict[str, int] = field(default_factory=dict)
    tool_error_count: dict[str, int] = field(default_factory=dict)
    llm_call_count: dict[str, int] = field(default_factory=dict)
    llm_durations: dict[str, list[float]] = field(default_factory=dict)

    def record_pipeline_duration(self, duration: float) -> None:
        self.pipeline_durations.append(duration)

    def record_plugin_duration(self, plugin: str, stage: str, duration: float) -> None:
        key = f"{stage}:{plugin}"
        self.plugin_durations.setdefault(key, []).append(duration)

    def record_tool_execution(
        self, tool_name: str, stage: str, pipeline_id: str, result_key: str, source: str
    ) -> None:
        key = f"{stage}:{tool_name}"
        self.tool_execution_count[key] = self.tool_execution_count.get(key, 0) + 1

    def record_tool_error(
        self, tool_name: str, stage: str, pipeline_id: str, error: str
    ) -> None:
        key = f"{stage}:{tool_name}"
        self.tool_error_count[key] = self.tool_error_count.get(key, 0) + 1

    def record_llm_call(self, plugin: str, stage: str, purpose: str) -> None:
        key = f"{stage}:{plugin}:{purpose}"
        self.llm_call_count[key] = self.llm_call_count.get(key, 0) + 1

    def record_llm_duration(self, plugin: str, stage: str, duration: float) -> None:
        key = f"{stage}:{plugin}"
        self.llm_durations.setdefault(key, []).append(duration)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_durations": self.pipeline_durations,
            "plugin_durations": self.plugin_durations,
            "tool_execution_count": self.tool_execution_count,
            "tool_error_count": self.tool_error_count,
            "llm_call_count": self.llm_call_count,
            "llm_durations": self.llm_durations,
        }


@dataclass
class PipelineState:
    conversation: List[ConversationEntry]
    response: Any = None
    prompt: str = ""
    stage_results: Dict[str, Any] = field(default_factory=dict)
    pending_tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    pipeline_id: str = ""
    current_stage: Optional[PipelineStage] = None
    metrics: MetricsCollector = field(default_factory=MetricsCollector)
    failure_info: Optional[FailureInfo] = None
