# Entity Pipeline Framework

[![Build Status](https://github.com/Ladvien/entity/actions/workflows/test.yml/badge.svg)](https://github.com/Ladvien/entity/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://entity.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Entity lets you craft agent pipelines using a single configuration file. The same YAML works locally and in production, so iteration stays simple. Conversations are persisted externally through the Memory resource, keeping workers stateless. The default DuckDB backend writes this data to disk for immediate durability while still requiring zero setup.

## Key Features
- Three-layer plugin system for progressive complexity
- Hot-reloadable YAML config with validation
- Stateless workers that scale horizontally
- Unified memory resource for chat, search, and storage
- DuckDB backend persists to disk for quick local testing
- Overrides of default plugin stages produce log warnings

### Plugin Context Helpers
Plugins can access canonical resources with helper methods:
`context.get_llm()`, `context.get_memory()`, and `context.get_storage()`.

Check the [hero landing page](https://entity.readthedocs.io/en/latest/) for a visual overview.

## Minimal Example
```bash
poetry run entity-cli --config config/dev.yaml
```

A typical configuration defines each resource separately:

```yaml
plugins:
  resources:
    database:
      type: entity.infrastructure.duckdb:DuckDBInfrastructure
      path: ./agent.duckdb
    vector_store:
      type: plugins.builtin.resources.duckdb_vector_store:DuckDBVectorStore
  agent_resources:
    memory:
      type: entity.resources.memory:Memory
      dependencies: [database, vector_store]
```

See the [Quick Start](docs/source/quick_start.md) for step-by-step setup or browse the [full documentation](https://entity.readthedocs.io/en/latest/).

### Zero-Config Plugins

Register a tool and prompt without specifying stages:

```python
from entity import Agent

agent = Agent()

@agent.tool
async def add(a: int, b: int) -> int:
    return a + b


@agent.prompt
async def final(ctx):
    result = await ctx.tool_use("add", a=2, b=2)
    ctx.say(str(result))
```
