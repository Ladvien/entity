# Entity Pipeline Framework

[![Build Status](https://github.com/Ladvien/entity/actions/workflows/test.yml/badge.svg)](https://github.com/Ladvien/entity/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://entity.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Entity lets you craft agent pipelines using a single configuration file. The same YAML works locally and in production, so iteration stays simple. Conversations are persisted externally through the Memory resource, keeping workers stateless. The default DuckDB backend writes this data to disk for immediate durability while still requiring zero setup.

All pipeline utilities are now provided under the ``entity.pipeline`` namespace. The old ``pipeline`` package remains as a thin wrapper for backward compatibility.

## Key Features
- Three-layer plugin system for progressive complexity
- Hot-reloadable YAML config with validation
- Stateless workers that scale horizontally
- Unified memory resource for chat, search, and storage
- DuckDB backend persists to disk for quick local testing
- Automatic metrics collection via a shared MetricsCollector resource
- Overrides of default plugin stages produce log warnings

### Plugin Context Helpers
Plugins can access canonical resources with helper methods:
`context.get_llm()`, `context.get_memory()`, and `context.get_storage()`.
Use `context.remember()`, `context.recall()`, and `context.forget()` to persist
small values across requests.

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

To make a dependency optional, append `?` to its name, e.g. `vector_store?`. Optional dependencies aren't validated during initialization and will be `None` if not configured.

See the [Quick Start](docs/source/quick_start.md) for step-by-step setup or browse the [full documentation](https://entity.readthedocs.io/en/latest/).

### Quick Start

The package exposes a default agent instance for quick experiments. It uses
Ollama for LLM calls, persists memory in `./agent_memory.duckdb`, and stores
files under `./agent_files`.

```python
from entity import agent

@agent.tool
async def add(a: int, b: int) -> int:
    return a + b


@agent.prompt
async def respond(ctx):
    result = await ctx.tool_use("add", a=2, b=2)
    ctx.say(str(result))

import asyncio
asyncio.run(agent.handle("calc"))
```

Ensure [Ollama](https://ollama.ai) is installed and run `ollama pull llama3` before testing.

### Stateless Workers (Decision 6)

Workers hold no conversation state between requests. Instead, the `Memory` resource persists data to an external store. Each worker loads the conversation from `Memory` at the start of a request and saves updates when finished. This allows any worker process to handle any user without coordination.

The default configuration persists `Memory` through DuckDB:

```yaml
agent_resources:
  memory:
    type: entity.resources.memory:Memory
    dependencies: [database]
```

See [`config/dev.yaml`](config/dev.yaml) for the complete example.

### Zero-Config Plugins

Register a tool and output plugin using the default ``agent`` instance.
The output plugin emits the final response:

```python
from entity import agent

@agent.tool
async def add(a: int, b: int) -> int:
    return a + b


@agent.output
async def final(ctx):
    result = await ctx.tool_use("add", a=2, b=2)
    ctx.say(str(result))
```
## Development Environment Setup

This project uses `mise` for Python version management. The `.python-version` file specifies the required interpreter. The `.mise.toml` config explicitly enables this file so future `mise` releases won't warn about idiomatic version files. After installing `mise`, run:

```bash
mise install
```


## Examples

The repository includes two sample agents:

- [`examples/kitchen_sink`](examples/kitchen_sink) – a full-featured demo using several plugins.
- [`examples/zero_config_agent`](examples/zero_config_agent) – minimal setup with the default agent.
