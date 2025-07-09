from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MetricsCollector:
    """Collect timing and count metrics."""

    stage_durations: Dict[str, float] = field(default_factory=dict)
    plugin_durations: Dict[str, List[float]] = field(default_factory=dict)
    llm_durations: Dict[str, List[float]] = field(default_factory=dict)
    llm_call_count: Dict[str, int] = field(default_factory=dict)
    tool_durations: Dict[str, List[float]] = field(default_factory=dict)
    tool_execution_count: Dict[str, int] = field(default_factory=dict)
    pipeline_durations: List[float] = field(default_factory=list)

    def record_stage_duration(self, stage: str, duration: float) -> None:
        self.stage_durations[stage] = duration

    def record_plugin_duration(self, plugin: str, duration: float) -> None:
        self.plugin_durations.setdefault(plugin, []).append(duration)

    def record_llm_duration(self, key: str, duration: float) -> None:
        self.llm_durations.setdefault(key, []).append(duration)
        self.llm_call_count[key] = self.llm_call_count.get(key, 0) + 1

    def record_tool_duration(self, key: str, duration: float) -> None:
        self.tool_durations.setdefault(key, []).append(duration)
        self.tool_execution_count[key] = self.tool_execution_count.get(key, 0) + 1

    def record_pipeline_duration(self, duration: float) -> None:
        self.pipeline_durations.append(duration)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_durations": self.stage_durations,
            "plugin_durations": self.plugin_durations,
            "llm_durations": self.llm_durations,
            "llm_call_count": self.llm_call_count,
            "tool_durations": self.tool_durations,
            "tool_execution_count": self.tool_execution_count,
            "pipeline_durations": self.pipeline_durations,
        }
