# Observability Experiment

This example shows how to expose Prometheus metrics and export OpenTelemetry
traces for a minimal pipeline.

Run the demo:

```bash
poetry run python experiments/observability/simple_pipeline.py
```

Set `OTEL_EXPORTER_OTLP_ENDPOINT` before running to send spans to a collector.
Prometheus can scrape metrics from `http://localhost:9001/metrics`.
