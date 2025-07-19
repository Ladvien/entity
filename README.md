# Entity Pipeline Framework

[![Build Status](https://github.com/Ladvien/entity/actions/workflows/test.yml/badge.svg)](https://github.com/Ladvien/entity/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://entity.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Plugin Tool

Generate a new prompt plugin:

```bash
plugin-tool generate my_prompt --type prompt
```

Run the plugin in isolation:

```bash
plugin-tool test src/my_prompt.py
```

Create Markdown docs from the plugin docstring:

```bash
plugin-tool docs src/my_prompt.py --out docs
```

## Default Workflow

`Layer0SetupManager` creates local resources and ships with a ready-made
`default_workflow`. The global `agent` picks up this workflow automatically,
so no extra configuration is required.

```python
import asyncio
from entity import agent
from entity.utils.setup_manager import Layer0SetupManager
from entity.workflows import default_workflow

# uses `default_workflow` when none is provided
asyncio.run(Layer0SetupManager().setup())
print(asyncio.run(agent.handle("Hello")))
```

## Example Plugins

Check the `src/plugins/examples` directory for minimal plugins demonstrating the
INPUT, PARSE, and REVIEW stages. Each shows how to interact with the
`PluginContext` during execution. These plugins are registered in the
`DefaultWorkflow` for quick experimentation. The rendered source is available in the
[Plugin Examples](https://entity.readthedocs.io/en/latest/plugin_examples.html)
documentation.

## Infrastructure Plugins

Register infrastructure plugins under the `database_backend` and `vector_store`
keys when configuring resources.

```yaml
plugins:
  infrastructure:
    postgres_backend:
      type: entity.infrastructure.asyncpg:AsyncPGInfrastructure
      dsn: postgresql://user:pass@localhost:5432/agent
  resources:
    vector_store:
      type: entity.resources.duckdb_vector_store:DuckDBVectorStore
```

## Metrics & Performance

Use the bundled `MetricsCollectorResource` to inspect plugin and resource activity.

```python
metrics = agent.get_resource("metrics_collector")
log = await metrics.get_unified_agent_log("my_agent")
summary = await metrics.get_performance_summary("my_agent")
```

## Running Tests

The test suite depends on **Docker** and the **`pytest-docker`** plugin.
After cloning the repository, **copy `.env.example` to `.env`**, trust the local
`mise` configuration, and install the development dependencies. Set
`POSTGRES_READY_TIMEOUT` in this file if the database container takes longer to
become healthy:

```bash
mise trust
poetry install --with dev
```

With Docker running, use the Poe task below to spin up services and run the full
test suite. The task runs a shell script that tears down containers even if the
tests fail:

```bash
poetry run poe test-with-docker
```

To run only the architecture boundary checks, use:

```bash
poetry run poe test-layer-boundaries
```

`pytest-docker` is required for the integration fixtures. It is installed with
the development dependencies shown above. If you installed packages
individually, install the plugin directly:

```bash
pip install pytest-docker
```

### Install Docker

Follow the [official Docker installation guide](https://docs.docker.com/get-docker/) for your platform. After installing, confirm Docker works:

```bash
docker --version
```

If Docker isn't available, the integration tests will be skipped automatically.

### Docker Requirement for Integration Tests

Integration tests rely on containers defined in `tests/docker-compose.yml`.
If Docker isn't running, `pytest-docker` automatically marks these tests as
skipped so the rest of the suite can continue.

Before starting Docker, **copy `.env.example` to `.env`** and adjust the values
for your local setup. You can set `POSTGRES_READY_TIMEOUT` here if you need to
wait longer for the database container. The compose files read this file
automatically.

The Postgres service uses the `pgvector/pgvector:pg16` image so the `vector`
extension is available without additional setup.

### Integration Tests & Docker

Integration tests spin up containers defined in `tests/docker-compose.yml`.

`pytest-docker` exposes the `docker_ip` and `docker_services` fixtures used by
the integration tests. Make sure the optional dependencies `pyyaml` and
`python-dotenv` are available to avoid runtime import errors when the CLI loads
YAML configurations.

For detailed output, use the verbose task:

```bash
poe test-verbose
```

If you prefer calling `pytest` directly, prepend `PYTHONPATH=src` so Python can
locate the editable package:

```bash
PYTHONPATH=src pytest
```

## Multi-User Support

Pass a unique `user_id` when calling `agent.chat()` or `agent.handle()` to keep
conversation history and memory isolated per user.

```python
response = await agent.chat("Hi", user_id="alice")
```

See [multi_user](docs/source/multi_user.md) for additional patterns.

