# Structured Logging

The easiest way to capture structured logs is using ``LoggingAdapter``. Add it
to your ``adapters`` configuration or initialize it directly:

```python
from plugins.builtin.adapters.logging import LoggingAdapter

adapter = LoggingAdapter()
```

Every pipeline run generates a unique *request ID*. When using
``LoggingAdapter`` this ID is
attached to each log entry under the `request_id` field.

Plugins can access the same value via `context.request_id`.

Example log output:

```json
{"timestamp": "2025-05-05T12:00:00", "level": "INFO", "name": "MyPlugin", "message": "Plugin execution finished", "plugin": "MyPlugin", "stage": "DO", "duration": 0.2, "request_id": "202505051200000000"}
```

Use the ID to trace a single request across plugins and stages.

### Example Script

The `examples/structured_logging_example.py` script initializes ``LoggingAdapter`` and writes a single log entry.
Run it with:

```bash
python examples/structured_logging_example.py
```

