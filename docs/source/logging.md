# Structured Logging

The easiest way to capture structured logs is using ``LoggingAdapter``. Add it
to your ``adapters`` configuration or initialize it directly:

```python
# from entity.plugins.builtin.adapters.logging import LoggingAdapter

# adapter = LoggingAdapter()
```

To configure logging globally, call ``configure_logging`` from
``entity.plugins.builtin.adapters.logging_adapter``:

```python
# from entity.plugins.builtin.adapters.logging_adapter import configure_logging, get_logger

# configure_logging(level="INFO", json_enabled=True)
# logger = get_logger(__name__)
# logger.info("Logging configured")
```

Set the ``ENTITY_LOG_PATH`` environment variable to route logs to a file.

Every pipeline run generates a unique *request ID*. When using
``LoggingAdapter`` this ID is
attached to each log entry under the `request_id` field.

Plugins can access the same value via `context.request_id`.

Example log output:

```json
{"timestamp": "2025-05-05T12:00:00", "level": "INFO", "name": "MyPlugin", "message": "Plugin execution finished", "plugin": "MyPlugin", "stage": "DO", "duration": 0.2, "request_id": "202505051200000000"}
```

Use the ID to trace a single request across plugins and stages.


## Plugin and Tool Observability

Each plugin executed by the pipeline automatically logs start and finish events.
Messages include the plugin name, stage and request ID so entries can be
correlated across stages. Tool executions follow the same pattern. When a tool
starts, finishes or fails, a structured log entry is emitted describing the
result.

Metrics collection has been removed. Only structured logs are emitted.

For production deployments, `config/logging_prod.yaml` contains a recommended
configuration enabling JSON formatted logs and file rotation.

## Failure Logs

When a pipeline encounters an error the ``BasicLogger`` plugin emits an ``ERROR``
log entry. The message ``"Pipeline failure encountered"`` includes several extra
fields:

* ``stage`` – stage where the failure occurred
* ``plugin`` – name of the plugin that raised the error
* ``type`` – exception class name
* ``error`` – human readable message
* ``pipeline_id`` – unique identifier for the run
* ``retry_count`` – current iteration count
* ``context_snapshot`` – serialized pipeline state (always present but may be empty)

These fields provide enough information to correlate failures with pipeline
state and retry attempts.

