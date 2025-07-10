# Debugging the Pipeline

This page explains how to enable verbose logging, resolve common issues, and inspect performance.

## Enabling debug logs

Set `LOG_LEVEL=DEBUG` when running `entity-cli` or your custom entrypoint. You can also call `configure_logging(level="DEBUG")` from `LoggingAdapter` to override the level at runtime.

Enable `json_enabled` to capture structured fields:

```python
from entity.plugins.builtin.adapters.logging_adapter import configure_logging

configure_logging(level="DEBUG", json_enabled=True)
```

Debug logs include the request ID, plugin name, and stage so you can trace a single run end-to-end.

## Common error patterns

- **Validation failures** – run `poetry run entity-cli --config your.yaml` with `LOG_LEVEL=DEBUG` to print the exact field causing the error.
- **Plugin import errors** – verify the import path and that the module is on `PYTHONPATH`.
- **Missing resources** – check that every dependency listed in a plugin's configuration appears under `resources:`.

When unsure, run the unit tests with `poetry run pytest -vv` to reproduce issues locally.

## Monitoring performance and resource usage

Use `MetricsServerManager.start()` to expose Prometheus metrics and CPU/memory gauges. The `/dashboard` endpoint offers a lightweight UI for development. For more details, see [Monitoring the Pipeline](monitoring.md).
