from __future__ import annotations

"""Telemetry stubs for future metrics integration."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MetricsCollector:
    """Placeholder metrics collector."""

    stage_durations: Dict[str, float] = field(default_factory=dict)

    def record_stage_duration(self, stage: str, duration: float) -> None:
        self.stage_durations[stage] = duration

    def record_tool_duration(
        self, key: str, duration: float
    ) -> None:  # pragma: no cover - stub
        pass

    def record_plugin_duration(
        self, key: str, duration: float
    ) -> None:  # pragma: no cover - stub
        pass

    def record_llm_duration(
        self, key: str, duration: float
    ) -> None:  # pragma: no cover - stub
        pass

    def record_pipeline_duration(
        self, duration: float
    ) -> None:  # pragma: no cover - stub
        pass


__all__ = ["MetricsCollector"]
