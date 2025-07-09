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
    postgres:
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
    storage:
      type: storage
      dependencies: [postgres, vector_store, filesystem]
```

`MemoryResource` persists conversation history and vectors. `StorageResource` extends it with file CRUD across the configured backends.

For local experimentation you can use a file-backed DuckDB database:

```yaml
plugins:
  resources:
    db:
      type: plugins.builtin.resources.duckdb_database:DuckDBDatabaseResource
      path: ./agent.duckdb
    storage:
      type: storage
      dependencies: [db]
```

You can also use `StorageResource` for a lighter setup:

```yaml
plugins:
  resources:
    db:
      type: plugins.builtin.resources.duckdb_database:DuckDBDatabaseResource
      path: ./agent.duckdb
    fs:
      type: plugins.builtin.resources.local_filesystem:LocalFileSystemResource
      base_path: ./files
    storage:
      type: storage
      dependencies: [db, fs]
```

These configurations illustrate **Preserve All Power (7)** by enabling
advanced storage without sacrificing the simple default setup.

### Runtime Configuration Reload

Update plugin settings without restarting the agent:

```bash
poetry run python src/cli.py reload-config updated.yaml
```

The command waits for active pipelines to finish, then applies the new YAML
configuration. **Only parameter updates to existing plugins can be reloaded.**
Any structural change—adding or removing plugins, modifying stage assignments, or
changing dependencies—requires restarting the agent. This keeps hot reloads fast
for tunable values while preventing inconsistent pipeline state.

For a hands-on demonstration, run `examples/config_reload_example.py`:

```bash
python examples/config_reload_example.py
```

### Runtime Reconfiguration and Rollback

`update_plugin_configuration()` applies parameter changes at runtime. If a
plugin reports that a restart is required the function returns
`requires_restart` and no updates are applied. If a dependent plugin rejects a
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
