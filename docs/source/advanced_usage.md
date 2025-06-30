```{include} ../../README.md
:relative-images:
:start-after: <!-- start advanced_usage -->
:end-before: <!-- end advanced_usage -->
```

### Enabling pgvector Storage

PostgreSQL's `pgvector` extension allows vector similarity search for embeddings.
Add a setup command in your configuration to enable the extension and register a
vector-aware memory plugin.

```yaml
plugins:
  resources:
    database:
      type: postgres
      host: localhost
      port: 5432
      name: dev_db
      username: agent
      setup_commands:
        - "CREATE EXTENSION IF NOT EXISTS vector"
  prompts:
    vector_memory:
      type: vector_memory
      dependencies: ["database"]
```

For a working example, see
[`vector_memory_pipeline.py`](../../examples/vector_memory_pipeline.py).
