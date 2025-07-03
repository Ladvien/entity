# Structured Logging

The framework exposes a simple helper to enable JSON logs for any deployment.
Enable logging at startup:

```python
from pipeline.logging import configure_logging

configure_logging(level="INFO", json_enabled=True)
```

Every pipeline run generates a unique *request ID*. When using
`configure_logging` or the `StructuredLogging` resource plugin, this ID is
attached to each log entry under the `request_id` field.

Plugins can access the same value via `context.request_id`.

Example log output:

```json
{"timestamp": "2025-05-05T12:00:00", "level": "INFO", "name": "MyPlugin", "message": "Plugin execution finished", "plugin": "MyPlugin", "stage": "DO", "duration": 0.2, "request_id": "202505051200000000"}
```

Use the ID to trace a single request across plugins and stages.
