# Entity Documentation

Welcome to the Entity pipeline framework documentation.

The pipeline implementation now lives under the ``entity.pipeline`` package. Imports from ``pipeline`` will continue to work but emit a deprecation warning.

```{toctree}
:maxdepth: 2
:hidden:
error_handling
logging
```

The following pages cover core concepts and usage patterns.

## LoggingResource

The `LoggingResource` provides structured logging across all pipeline components. It supports multiple outputs like console, JSON files, and real-time streams.

```yaml
plugins:
  resources:
    logging:
      type: entity.resources.logging:LoggingResource
      outputs:
        - type: console
          level: info
        - type: structured_file
          level: debug
          path: logs/entity.jsonl
```

## MetricsCollectorResource

`MetricsCollectorResource` collects performance and custom metrics from every plugin. The resource is automatically added if not specified.

```yaml
plugins:
  resources:
    metrics_collector:
      type: entity.resources.metrics_collector:MetricsCollectorResource
      retention_days: 90
      buffer_size: 1000
```
