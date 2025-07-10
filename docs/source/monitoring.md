# Monitoring the Pipeline

This guide shows how to collect metrics and traces from an Entity deployment.


## OpenTelemetry Tracing

Wrap tasks with `start_span()` to emit traces. When the
`OTEL_EXPORTER_OTLP_ENDPOINT` environment variable is set, spans are exported to
that OTLP endpoint; otherwise they are printed to the console.

```python
from pipeline.observability import start_span

async with start_span("my_task"):
    await do_work()
```


## Grafana Dashboard

Below is a minimal dashboard JSON you can import into Grafana:

```json
{
  "title": "Entity Overview",
  "panels": [
    {"type": "graph", "title": "LLM Latency", "targets": [{"expr": "llm_latency_seconds"}]},
    {"type": "graph", "title": "LLM Failures", "targets": [{"expr": "llm_failures_total"}]}
  ]
}
```

Save it as `entity_dashboard.json` and import through the Grafana UI.

## Alert Rules

Create alerts in Prometheus for high latency or failures:

```yaml
- alert: LLMHighLatency
  expr: llm_latency_seconds_bucket{le="5"} > 0
  for: 1m
  labels:
    severity: warning
  annotations:
    description: "LLM calls are taking more than five seconds"

- alert: LLMFailures
  expr: increase(llm_failures_total[5m]) > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    description: "LLM failures detected"
```

## Health Checks

HTTP services expose a `/health` endpoint that reports the status of every
registered resource. The endpoint returns `{"status": "ok"}` when all resources
report healthy and `{"status": "error"}` otherwise. Use this for container
liveness probes and external monitoring.
