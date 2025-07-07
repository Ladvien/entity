from __future__ import annotations

"""Prometheus metrics integration for the Entity pipeline."""

import psutil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)

from pipeline.metrics import MetricsCollector

__all__ = ["MetricsServer", "start_metrics_server", "get_metrics_server"]


class MetricsServer:
    """Expose pipeline metrics via Prometheus."""

    def __init__(self, port: int = 9001) -> None:
        self.registry = CollectorRegistry()
        self.llm_latency = Histogram(
            "llm_latency_seconds",
            "Latency of LLM calls",
            ["plugin", "stage"],
            registry=self.registry,
        )
        self.llm_failures = Counter(
            "llm_failures_total",
            "Number of failed LLM calls",
            ["plugin", "stage"],
            registry=self.registry,
        )
        self.stage_duration = Histogram(
            "stage_duration_seconds",
            "Duration of each pipeline stage",
            ["stage"],
            registry=self.registry,
        )
        self.cpu_usage = Gauge(
            "process_cpu_percent",
            "Process CPU utilization percent",
            registry=self.registry,
        )
        self.mem_usage = Gauge(
            "process_memory_bytes",
            "Process memory usage in bytes",
            registry=self.registry,
        )
        self.dashboard_requests = Counter(
            "dashboard_requests_total",
            "Number of dashboard requests",
            registry=self.registry,
        )
        start_http_server(port, registry=self.registry)

    def update(self, metrics: MetricsCollector) -> None:
        """Update Prometheus values from ``metrics``."""
        for key, durations in metrics.llm_durations.items():
            stage, plugin = key.split(":", 1)
            for d in durations:
                self.llm_latency.labels(plugin=plugin, stage=stage).observe(d)
        for key, count in metrics.tool_error_count.items():
            stage, plugin = key.split(":", 1)
            self.llm_failures.labels(plugin=plugin, stage=stage).inc(count)
        for stage, durations in metrics.stage_durations.items():
            for d in durations:
                self.stage_duration.labels(stage=stage).observe(d)
        self.cpu_usage.set(psutil.cpu_percent())
        self.mem_usage.set(psutil.Process().memory_info().rss)
        self.dashboard_requests.inc(metrics.dashboard_requests)

    def render(self) -> bytes:
        """Return metrics in Prometheus text format."""
        return generate_latest(self.registry)


_metrics_server: MetricsServer | None = None


def get_metrics_server() -> MetricsServer | None:
    """Return the current metrics server instance if running."""
    return _metrics_server


def start_metrics_server(port: int = 9001) -> MetricsServer:
    """Start the Prometheus metrics HTTP server."""
    global _metrics_server
    if _metrics_server is None:
        _metrics_server = MetricsServer(port)
    return _metrics_server
