# Entity Framework
Python agent framework

## Examples
Run `python -m entity.examples` to see sample workflows. The old `[examples]` extra has been removed.

## Persistent Memory

Entity uses a DuckDB database to store all remembered values. Keys are
namespaced by user ID to keep data isolated between users. The `Memory` API is
asynchronous and protected by an internal lock so concurrent workflows remain
thread safe.

## Stateless Scaling

Because all user data lives in the `Memory` resource, multiple workers can
share the same database file without keeping any local state. Start several
processes pointing at the same DuckDB path to horizontally scale:

```bash
ENTITY_DUCKDB_PATH=/data/agent.duckdb python -m entity.examples &
ENTITY_DUCKDB_PATH=/data/agent.duckdb python -m entity.examples &
```

Connection pooling in `DuckDBInfrastructure` allows many concurrent users to
read and write without exhausting file handles.

## Plugin Lifecycle

Plugins are validated before any workflow executes:

1. **Configuration validation** – each plugin defines a `ConfigModel` and the
   `validate_config` classmethod parses user options with Pydantic.
2. **Workflow validation** – `validate_workflow` is called when workflows are
   built to ensure a plugin supports its assigned stage.
3. **Execution** – once instantiated with resources, validated plugins run
   without further checks.

Entity stores all remembered values inside a DuckDB database. Keys are
automatically prefixed with the user ID so data never leaks across users. The
`Memory` API exposes asynchronous helpers that run queries in a background
thread while holding an internal `asyncio.Lock`.

```python
infra = DuckDBInfrastructure("agent.db")
memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
await memory.store("bob:greeting", "hello")
```

## Configuration via Environment Variables

`load_defaults()` reads a few environment variables when building default resources:

| Variable | Default |
| --- | --- |
| `ENTITY_DUCKDB_PATH` | `./agent_memory.duckdb` |
| `ENTITY_OLLAMA_URL` | `http://localhost:11434` |
| `ENTITY_OLLAMA_MODEL` | `llama3.2:3b` |
| `ENTITY_STORAGE_PATH` | `./agent_files` |

Services are checked for availability when defaults are built. If a component is
unreachable, an in-memory or stub implementation is used so the framework still
starts:

```bash
ENTITY_DUCKDB_PATH=/data/db.duckdb \
ENTITY_OLLAMA_URL=http://ollama:11434 \
ENTITY_STORAGE_PATH=/data/files \
python -m entity.examples
```

### Environment Variable Substitution

Configuration files support `${VAR}` references. Values are resolved using the
current environment and variables defined in a local `.env` file if present.
Nested references are expanded recursively and circular references raise a
`ValueError`.

```yaml
resources:
  database:
    host: ${DB_HOST}
    password: ${DB_PASS}
```

You can resolve placeholders in Python using `substitute_variables`:

```python
from entity.config import substitute_variables

config = substitute_variables({"endpoint": "${DB_HOST}/api"})
```
