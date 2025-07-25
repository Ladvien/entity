# Entity Framework
Entity is a Python framework for building AI agents. It runs locally by default and sets up resources automatically.

## Examples
<<<<<<< HEAD

=======
>>>>>>> pr-1930
Run `python examples/zero_config_agent.py` for a minimal CLI demo or
`python examples/advanced_workflow.py` to see a multi-stage workflow in action.
Resources are prepared automatically using ``load_defaults()`` so Docker is no
longer required for these examples.
The old `[examples]` extra has been removed.

### Workflow Templates

Parameterized workflow templates live in `entity.workflow.templates`.
Load them with custom values and visualize the result:

```python
from entity.workflow.templates import load_template
from entity.tools.workflow_viz import ascii_diagram

wf = load_template(
    "basic",
    think_plugin="entity.plugins.defaults.ThinkPlugin",
    output_plugin="entity.plugins.defaults.OutputPlugin",
)
print(ascii_diagram(wf))
```

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

## Observability

Logs are captured using `LoggingResource` which stores structured entries as
JSON dictionaries. Each entry contains a UTC timestamp, log level and any
additional fields supplied by the caller:

```python
{
    "level": "info",
    "message": "plugin_start",
    "timestamp": "2024-05-01T12:00:00Z",
    "fields": {"stage": "think", "plugin_name": "MyPlugin"}
}
```

Execution metrics are aggregated by `MetricsCollectorResource`. The collector
stores individual records and keeps running totals per plugin and stage:

```python
{
    "plugin_name": "MyPlugin",
    "stage": "think",
    "duration_ms": 12.4,
    "success": True
}
```

## Tool Security

Registered tools run inside a small sandbox that limits CPU time and memory.
Inputs and outputs can be validated with Pydantic models when registering a
function. Use `SandboxedToolRunner` to adjust limits.

To list available tools:

```python
from entity.tools import generate_docs
print(generate_docs())
```

## Running Tests

Install dependencies with Poetry and run the full suite:

```bash
poetry install --with dev
poetry run poe test
```

Integration tests rely on the services defined in `docker-compose.yml`.
Run them with Docker installed:

```bash
poetry run poe test-with-docker
```
This task brings the containers up, runs all tests marked `integration` in
parallel, and then tears the services down so no state is shared between runs.

## Advanced Setup

Optional services are provided in `docker-compose.yml`. Use them when you need Postgres or Ollama:

```bash
docker compose build ollama
docker compose up -d
# run agents or tests here
docker compose down -v
```
See `install_docker.sh` for an automated install script on Ubuntu. Detailed deployment steps live in `docs/production_deployment.md`. For help migrating away from Docker, check `docs/migration_from_docker.md`.
