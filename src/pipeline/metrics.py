from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsCollector:
    """Accumulates runtime metrics for a single pipeline run."""

    pipeline_durations: list[float] = field(default_factory=list)
    plugin_durations: dict[str, list[float]] = field(default_factory=dict)
    stage_durations: dict[str, list[float]] = field(default_factory=dict)
    tool_execution_count: dict[str, int] = field(default_factory=dict)
    tool_error_count: dict[str, int] = field(default_factory=dict)
    tool_durations: dict[str, list[float]] = field(default_factory=dict)
    llm_call_count: dict[str, int] = field(default_factory=dict)
    llm_durations: dict[str, list[float]] = field(default_factory=dict)
    llm_token_count: dict[str, int] = field(default_factory=dict)
    llm_cost: dict[str, float] = field(default_factory=dict)

    def record_pipeline_duration(self, duration: float) -> None:
        self.pipeline_durations.append(duration)

    def record_plugin_duration(self, plugin: str, stage: str, duration: float) -> None:
        key = f"{stage}:{plugin}"
        self.plugin_durations.setdefault(key, []).append(duration)

    def record_stage_duration(self, stage: str, duration: float) -> None:
        self.stage_durations.setdefault(stage, []).append(duration)

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

    def record_tool_duration(self, tool_name: str, stage: str, duration: float) -> None:
        key = f"{stage}:{tool_name}"
        self.tool_durations.setdefault(key, []).append(duration)

    def record_llm_call(self, plugin: str, stage: str, purpose: str) -> None:
        key = f"{stage}:{plugin}:{purpose}"
        self.llm_call_count[key] = self.llm_call_count.get(key, 0) + 1

    def record_llm_duration(self, plugin: str, stage: str, duration: float) -> None:
        key = f"{stage}:{plugin}"
        self.llm_durations.setdefault(key, []).append(duration)

    def record_llm_tokens(self, plugin: str, stage: str, tokens: int) -> None:
        key = f"{stage}:{plugin}"
        self.llm_token_count[key] = self.llm_token_count.get(key, 0) + tokens

    def record_llm_cost(self, plugin: str, stage: str, cost: float) -> None:
        key = f"{stage}:{plugin}"
        self.llm_cost[key] = self.llm_cost.get(key, 0.0) + cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_durations": self.pipeline_durations,
            "plugin_durations": self.plugin_durations,
            "stage_durations": self.stage_durations,
            "tool_execution_count": self.tool_execution_count,
            "tool_error_count": self.tool_error_count,
            "tool_durations": self.tool_durations,
            "llm_call_count": self.llm_call_count,
            "llm_durations": self.llm_durations,
            "llm_token_count": self.llm_token_count,
            "llm_cost": self.llm_cost,
        }
