from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List

from .base import AgentResource
from ..pipeline.stages import PipelineStage
from ..core.plugins import ValidationResult


class MetricsCollectorResource(AgentResource):  # type: ignore[misc]
    """In-memory metrics collector available to all plugins."""

    name = "metrics_collector"
    dependencies: List[str] = []

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.plugin_metrics: List[Dict[str, Any]] = []
        self.resource_metrics: List[Dict[str, Any]] = []
        self.custom_metrics: List[Dict[str, Any]] = []
        self.counters: Dict[str, int] = defaultdict(int)

    # ------------------------------------------------------------------
    # Core collection methods used by framework
    # ------------------------------------------------------------------
    async def record_plugin_execution(
        self,
        *,
        pipeline_id: str,
        stage: PipelineStage,
        plugin_name: str,
        duration_ms: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        self.plugin_metrics.append(
            {
                "pipeline_id": pipeline_id,
                "stage": stage,
                "plugin_name": plugin_name,
                "duration_ms": duration_ms,
                "success": success,
                "error_type": error_type,
                "timestamp": time.time(),
            }
        )

    async def record_resource_operation(
        self,
        *,
        pipeline_id: str,
        resource_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        self.resource_metrics.append(
            {
                "pipeline_id": pipeline_id,
                "resource_name": resource_name,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "metadata": metadata or {},
                "timestamp": time.time(),
            }
        )

    # ------------------------------------------------------------------
    # Plugin-facing methods for custom metrics
    # ------------------------------------------------------------------
    async def record_custom_metric(
        self,
        *,
        pipeline_id: str,
        metric_name: str,
        value: float,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        self.custom_metrics.append(
            {
                "pipeline_id": pipeline_id,
                "metric_name": metric_name,
                "value": value,
                "metadata": metadata or {},
                "timestamp": time.time(),
            }
        )

    async def increment_counter(
        self,
        *,
        pipeline_id: str,
        counter_name: str,
        increment: int = 1,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        self.counters[counter_name] += increment
        self.custom_metrics.append(
            {
                "pipeline_id": pipeline_id,
                "metric_name": counter_name,
                "value": self.counters[counter_name],
                "metadata": metadata or {},
                "timestamp": time.time(),
            }
        )

    # ------------------------------------------------------------------
    # Analytics and querying
    # ------------------------------------------------------------------
    async def get_unified_agent_log(
        self,
        *,
        pipeline_id: str | None = None,
        user_id: str | None = None,
        time_range: tuple[float, float] | None = None,
    ) -> List[Dict[str, Any]]:
        entries = self.plugin_metrics + self.resource_metrics + self.custom_metrics
        if pipeline_id is not None:
            entries = [e for e in entries if e.get("pipeline_id") == pipeline_id]
        if time_range is not None:
            start, end = time_range
            entries = [e for e in entries if start <= e.get("timestamp", 0) <= end]
        if user_id is not None:
            entries = [e for e in entries if e.get("user_id") == user_id]
        return list(entries)

    async def get_performance_summary(
        self, agent_name: str, hours: int = 24
    ) -> Dict[str, Any]:
        cutoff = time.time() - hours * 3600
        plugin_calls = [m for m in self.plugin_metrics if m["timestamp"] >= cutoff]
        resource_ops = [m for m in self.resource_metrics if m["timestamp"] >= cutoff]
        return {
            "agent": agent_name,
            "plugin_executions": len(plugin_calls),
            "resource_operations": len(resource_ops),
        }

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        return ValidationResult.success_result()
