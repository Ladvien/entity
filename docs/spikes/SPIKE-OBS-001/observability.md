# SPIKE-OBS-001: Observability Options

## Structured Logging
- **Python logging** with JSON formatting is already used in the project via `plugins.builtin.adapters.logging_adapter`.
- Each log message can include extra fields such as plugin, stage, and request ID for context.
- JSON logs integrate cleanly with aggregators like **Elastic Stack** or **Grafana Loki**.

## OpenTelemetry Tracing
- The `pipeline.observability.tracing` module wraps OpenTelemetry APIs.
- Spans are exported to an OTLP endpoint if `OTEL_EXPORTER_OTLP_ENDPOINT` is set; otherwise they print to console.
- Wrapping async functions with `start_span` or `traced` captures execution timing and nested relationships.

## Prometheus Metrics
- `pipeline.observability.metrics` exposes a `MetricsServer` that collects latency and failure counts.
- Calling `start_metrics_server(port=9001)` starts an HTTP endpoint at `/metrics` for Prometheus to scrape.
- CPU and memory gauges help identify resource bottlenecks.

## State Machine Visualization
- The **transitions** library can render state diagrams via Graphviz with `Machine.get_graph().draw()`.
- Tools like **plantuml** or **state-machine-cat** can convert textual descriptions into diagrams.
- Diagramming aids communication of pipeline stages and error flows.

## Takeaways
- Leverage existing logging and metrics modules; ensure they run early in application startup.
- Export traces to an observability backend for correlation with logs and metrics.
- Use diagram generation from `transitions` or external tools to document complex state flows.
