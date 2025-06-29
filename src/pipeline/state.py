from __future__ import annotations

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
    source: str


@dataclass
class FailureInfo:
    stage: str
    plugin_name: str
    error_type: str
    error_message: str
    original_exception: Exception
    context_snapshot: Dict[str, Any]
    timestamp: datetime


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
    response: Any
    prompt: str
    stage_results: Dict[str, Any]
    pending_tool_calls: List[ToolCall]
    metadata: Dict[str, Any]
    pipeline_id: str
    current_stage: Optional[PipelineStage]
    metrics: MetricsCollector
    failure_info: Optional[FailureInfo] = None
