from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from entity.core.plugins import ResourcePlugin
from entity.core.stages import PipelineStage


@dataclass
class PluginExecutionRecord:
    pipeline_id: str
    stage: PipelineStage | None
    plugin_name: str
    duration_ms: float
    success: bool
    error_type: Optional[str] = None


@dataclass
class ResourceOperationRecord:
    pipeline_id: str
    resource_name: str
    operation: str
    duration_ms: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomMetricRecord:
    pipeline_id: str
    metric_name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollectorResource(ResourcePlugin):
    """Simple in-memory metrics collector."""

    name = "metrics_collector"
    dependencies = ["database"]

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.plugin_executions: List[PluginExecutionRecord] = []
        self.resource_operations: List[ResourceOperationRecord] = []
        self.custom_metrics: List[CustomMetricRecord] = []
        self.counters: Dict[str, int] = {}

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    # ------------------------------------------------------------------
    # Recording methods
    # ------------------------------------------------------------------
    async def record_plugin_execution(
        self,
        *,
        pipeline_id: str,
        stage: PipelineStage | None,
        plugin_name: str,
        duration_ms: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        self.plugin_executions.append(
            PluginExecutionRecord(
                pipeline_id=pipeline_id,
                stage=stage,
                plugin_name=plugin_name,
                duration_ms=duration_ms,
                success=success,
                error_type=error_type,
            )
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
        self.resource_operations.append(
            ResourceOperationRecord(
                pipeline_id=pipeline_id,
                resource_name=resource_name,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                metadata=metadata or {},
            )
        )

    async def record_custom_metric(
        self,
        *,
        pipeline_id: str,
        metric_name: str,
        value: float,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        self.custom_metrics.append(
            CustomMetricRecord(
                pipeline_id=pipeline_id,
                metric_name=metric_name,
                value=value,
                metadata=metadata or {},
            )
        )

    async def increment_counter(
        self,
        *,
        pipeline_id: str,
        counter_name: str,
        increment: int = 1,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        key = f"{pipeline_id}:{counter_name}"
        self.counters[key] = self.counters.get(key, 0) + increment
        if metadata is not None:
            # store metadata as custom metric for traceability
            await self.record_custom_metric(
                pipeline_id=pipeline_id,
                metric_name=f"counter:{counter_name}",
                value=self.counters[key],
                metadata=metadata,
            )


__all__ = ["MetricsCollectorResource"]
