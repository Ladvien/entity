# Advanced Usage

### Composing Storage Backends

Local development uses a file-backed DuckDB database by default, so you can
experiment without running an external server. `StorageResource` composes the
database and optional file system into a single interface:

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

`Memory` persists conversation history and vectors. `StorageResource` extends it with file CRUD across the configured backends.
Upgrade to a Postgres-backed setup when you need a production database with `pgvector`:
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


You can also use `StorageResource` for a lighter setup:

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

These configurations illustrate **Preserve All Power (7)** by enabling
advanced storage without sacrificing the simple default setup.

### Runtime Configuration Reload

Update plugin settings without restarting the agent:

```bash
poetry run entity-cli reload-config updated.yaml
```

The command waits for active pipelines to finish, then applies the new YAML
configuration. **Only parameter updates to existing plugins can be reloaded.**
Any structural change—adding or removing plugins, modifying stage assignments, or
changing dependencies—requires restarting the agent. This keeps hot reloads fast
for tunable values while preventing inconsistent pipeline state.

### Configuration Validation

Validate a YAML file without launching the agent:

```bash
poetry run entity-cli validate --config config/dev.yaml
```

`SystemInitializer` loads all plugins and exits with a non-zero code on errors.


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
function calling. Earlier versions included a demo script showing these
features:


### Running the Example Servers

For a WebSocket server use the CLI:

```bash
poetry run entity-cli serve-websocket --config config/dev.yaml
```

Start the CLI adapter for a basic text interface:

```bash

`Memory` stores conversation history and key-value data. A removed example demonstrated a simple in-memory cache.
