# Entity Documentation

Welcome to the Entity pipeline framework documentation.

The pipeline implementation now lives under the ``entity.pipeline`` package. Imports from ``pipeline`` will continue to work but emit a deprecation warning.

```{toctree}
:maxdepth: 2
:hidden:
error_handling
logging
configuration
plugin_examples
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
      type: entity.resources.metrics:MetricsCollectorResource
      retention_days: 90
      buffer_size: 1000
```

All plugins declare a dependency on ``metrics_collector`` by default, ensuring
metrics are recorded without additional configuration.

## DatabaseResource

`DuckDBResource` provides a zero-config persistent database. It depends on the
automatically created DuckDB infrastructure and is registered if omitted.

```yaml
plugins:
  resources:
    database:
      type: plugins.builtin.resources.duckdb_resource:DuckDBResource
      path: ./agent.duckdb
```
