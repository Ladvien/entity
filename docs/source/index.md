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
examples
plugins
workflows
multi_user
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

`MetricsCollectorResource` collects performance and custom metrics from every plugin.
It is a canonical resource at layer 3. When configured it is injected into all
plugins automatically. If omitted the initializer logs a warning and metrics are
disabled.

```yaml
plugins:
  resources:
    metrics_collector:
      type: entity.resources.metrics:MetricsCollectorResource
      retention_days: 90
      buffer_size: 1000
```

When present, the collector is passed to each plugin automatically so they can
record execution metrics without extra configuration.

```python
metrics = agent.get_resource("metrics_collector")
log = await metrics.get_unified_agent_log("my_agent")
summary = await metrics.get_performance_summary("my_agent")
```

`log` contains plugin and resource events. `summary` aggregates basic timing
stats per plugin.

## DatabaseResource

`DuckDBResource` provides a zero-config persistent database. It depends on the
automatically created `database` infrastructure and is registered if omitted.

```yaml
plugins:
  resources:
    database:
      type: entity.resources.database:DuckDBResource
      path: ./agent.duckdb
```

## VectorStoreResource

`VectorStoreResource` adds semantic search using a pluggable vector store. The
<<<<<<< HEAD
<<<<<<< HEAD
bundled `DuckDBVectorStore` registers at **layer 2** and relies on a dedicated
`vector_store_backend` infrastructure.
=======
bundled `DuckDBVectorStore` registers at **layer 2** and relies on the same
`database` infrastructure.
>>>>>>> pr-1816
=======
bundled `DuckDBVectorStore` registers at **layer 2** and depends on the
`vector_store_backend` infrastructure.
>>>>>>> pr-1820

```yaml
plugins:
  infrastructure:
    vector_store_backend:
      type: entity.infrastructure.duckdb_vector:DuckDBVectorInfrastructure
  resources:
    vector_store:
      type: entity.resources.duckdb_vector_store:DuckDBVectorStore
```
