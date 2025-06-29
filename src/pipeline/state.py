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


@dataclass
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
    """Placeholder metrics collector."""

    def record_plugin_duration(self, plugin: str, stage: str, duration: float) -> None:
        pass

    def record_tool_execution(
        self, tool_name: str, stage: str, pipeline_id: str, result_key: str, source: str
    ) -> None:
        pass

    def record_tool_error(
        self, tool_name: str, stage: str, pipeline_id: str, error: str
    ) -> None:
        pass

    def record_llm_call(self, plugin: str, stage: str, purpose: str) -> None:
        pass


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
