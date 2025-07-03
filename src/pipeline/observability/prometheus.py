from __future__ import annotations

"""Prometheus metrics exporter."""

from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Counter,
                               Summary, generate_latest)

from ..metrics import MetricsCollector


class PrometheusExporter:
    """Expose :class:`MetricsCollector` data as Prometheus metrics."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self.registry = registry
        self.pipeline_duration = Summary(
            "pipeline_duration_seconds",
            "Duration of pipeline runs in seconds",
            registry=registry,
        )
        self.plugin_duration = Summary(
            "plugin_duration_seconds",
            "Duration of plugin executions",
            ["stage", "plugin"],
            registry=registry,
        )
        self.tool_execution = Counter(
            "tool_executions_total",
            "Tool executions",
            ["stage", "tool"],
            registry=registry,
        )
        self.tool_errors = Counter(
            "tool_errors_total",
            "Tool execution errors",
            ["stage", "tool"],
            registry=registry,
        )
        self.llm_calls = Counter(
            "llm_calls_total",
            "LLM calls",
            ["stage", "plugin", "purpose"],
            registry=registry,
        )
        self.llm_duration = Summary(
            "llm_duration_seconds",
            "LLM call duration",
            ["stage", "plugin"],
            registry=registry,
        )

    def record(self, metrics: MetricsCollector) -> None:
        for duration in metrics.pipeline_durations:
            self.pipeline_duration.observe(duration)
        for key, durations in metrics.plugin_durations.items():
            stage, plugin = key.split(":", 1)
            for dur in durations:
                self.plugin_duration.labels(stage, plugin).observe(dur)
        for key, count in metrics.tool_execution_count.items():
            stage, tool = key.split(":", 1)
            self.tool_execution.labels(stage, tool).inc(count)
        for key, count in metrics.tool_error_count.items():
            stage, tool = key.split(":", 1)
            self.tool_errors.labels(stage, tool).inc(count)
        for key, count in metrics.llm_call_count.items():
            stage, plugin, purpose = key.split(":", 2)
            self.llm_calls.labels(stage, plugin, purpose).inc(count)
        for key, durations in metrics.llm_durations.items():
            stage, plugin = key.split(":", 1)
            for dur in durations:
                self.llm_duration.labels(stage, plugin).observe(dur)

    def generate_latest(self) -> bytes:
        return generate_latest(self.registry)


__all__ = ["PrometheusExporter", "CONTENT_TYPE_LATEST"]
