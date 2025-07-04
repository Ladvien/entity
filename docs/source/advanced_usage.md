```{include} ../../README.md
:relative-images:
:start-after: <!-- start advanced_usage -->
:end-before: <!-- end advanced_usage -->
```

### Composing Memory Backends

PostgreSQL's `pgvector` extension allows vector similarity search for embeddings.
Use `MemoryResource` with a Postgres database and optional S3 file storage:

```yaml
plugins:
  resources:
    memory:
      type: memory
      database:
        type: plugins.postgres:PostgresResource
        host: localhost
        port: 5432
        name: dev_db
        username: agent
        setup_commands:
          - "CREATE EXTENSION IF NOT EXISTS vector"
      vector_store:
        type: plugins.pg_vector_store:PgVectorStore
        dimensions: 768
        table: embeddings
      filesystem:
        type: plugins.s3_filesystem:S3FileSystem
        bucket: agent-files
        region: us-east-1
```

For local experimentation you can swap the database section with SQLite:

```yaml
plugins:
  resources:
    memory:
      type: memory
      database:
        type: plugins.sqlite_storage:SQLiteStorageResource
        path: ./agent.db
```

These configurations illustrate **Preserve All Power (7)** by enabling
advanced storage without sacrificing the simple default setup.

### Runtime Configuration Reload

Update plugin settings without restarting the agent:

```bash
python -m src.cli reload-config updated.yaml
```

The command waits for active pipelines to finish, then applies the new YAML
configuration. This demonstrates **Dynamic Configuration Updates**, letting you
tweak resources or tools at runtime while keeping the system responsive.

### Streaming and Function Calling

UnifiedLLMResource now exposes streaming via Server-Sent Events and optional
function calling. Run the `examples/advanced_llm.py` script to see these
features in action:

```bash
python examples/advanced_llm.py
```
