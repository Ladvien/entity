```{include} ../../README.md
:relative-images:
:start-after: <!-- start advanced_usage -->
:end-before: <!-- end advanced_usage -->
```

### Composing Storage Backends

PostgreSQL's `pgvector` extension allows vector similarity search for embeddings.
Use `StorageResource` with a Postgres database and optional S3 file storage:

```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.postgres:PostgresResource
        host: localhost
        port: 5432
        name: dev_db
        username: agent
        setup_commands:
          - "CREATE EXTENSION IF NOT EXISTS vector"
      vector_store:
        type: plugins.builtin.resources.pg_vector_store:PgVectorStore
        dimensions: 768
        table: embeddings
      filesystem:
        type: plugins.builtin.resources.s3_filesystem:S3FileSystem
        bucket: agent-files
        region: us-east-1
```

`MemoryResource` persists conversation history and vectors. `StorageResource` extends it with file CRUD across the configured backends.

For local experimentation you can use a file-backed DuckDB database:

```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.duckdb_database:DuckDBDatabaseResource
        path: ./agent.duckdb
```

You can also use `StorageResource` for a lighter setup:

```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.duckdb_database:DuckDBDatabaseResource
        path: ./agent.duckdb
      filesystem:
        type: plugins.builtin.resources.local_filesystem:LocalFileSystemResource
        base_path: ./files
```

These configurations illustrate **Preserve All Power (7)** by enabling
advanced storage without sacrificing the simple default setup.

### Runtime Configuration Reload

Update plugin settings without restarting the agent:

```bash
poetry run python src/cli.py reload-config updated.yaml
```

The command waits for active pipelines to finish, then applies the new YAML
configuration. Only parameter updates to **existing plugins** are hot reloadable;
adding plugins or changing their stages or dependencies requires a full
restart. This demonstrates **Dynamic Configuration Updates** for tunable values
while keeping the system responsive.

For a hands-on demonstration, run `examples/config_reload_example.py`:

```bash
python examples/config_reload_example.py
```

### Runtime Reconfiguration and Rollback

`update_plugin_configuration()` restarts plugins when necessary and validates
their dependencies before applying new settings. If a dependent plugin rejects a
change the framework rolls back to the previous configuration. Plugins expose a
`config_version` and `rollback_config()` helper:

```python
result = await update_plugin_configuration(reg.plugins, "my_plugin", {"value": 2})
if not result.success:
    print(result.error_message)
await reg.get_plugin("my_plugin").rollback_config()
```

### Streaming and Function Calling

UnifiedLLMResource now exposes streaming via Server-Sent Events and optional
function calling. Run the `examples/advanced_llm.py` script to see these
features in action:

```bash
python examples/advanced_llm.py
```

### Running the Example Servers

Start the demo HTTP server:

```bash
python examples/servers/http_server.py
```

For a WebSocket server use the CLI:

```bash
poetry run python src/cli.py serve-websocket --config config/dev.yaml
```

Run the gRPC server:

```bash
python examples/servers/grpc_server.py
```

Start the CLI adapter for a basic text interface:

```bash
python examples/servers/cli_adapter.py
```

### DuckDB Pipeline Example

The `examples/pipelines/duckdb_pipeline.py` script demonstrates a local vector
store backed by DuckDB:

```bash
python examples/pipelines/duckdb_pipeline.py
```

### Caching Pipeline Data

`CacheResource` lets plugins store intermediate results between stages. Configure it with `InMemoryCache` or your own backend. Run `examples/cache_example.py` for a minimal setup.
