# Writing Plugins

The Entity framework is built around extensible plugins. Plugins run during specific pipeline stages and interact with the system through `PluginContext`. Built-in plugin modules live under the `src/plugins` directory.

## Basic Class Plugin

Create a plugin class that inherits from one of the base plugin types and implement `_execute_impl`:

```python
from pipeline.base_plugins import PromptPlugin
from pipeline.stages import PipelineStage


class HelloPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.say("Hello from a plugin!")
```

Register the plugin with an `Agent` instance:

```python
from pipeline import Agent

agent = Agent()
agent.add_plugin(HelloPlugin({}))
```

## Function Plugin

You can also register an async function using the `@agent.plugin` decorator. The framework will automatically classify it and wrap it in a plugin object.

```python
agent = Agent()

@agent.plugin
async def weather_plugin(ctx):
    return await ctx.tool_use("weather", city="London")
```

### Stage Override Patterns

Plugin stages are resolved in a predictable order:

1. Stages defined in YAML or as a ``stages`` attribute on the class.
2. Defaults based on plugin type (``ToolPlugin`` → ``DO``, ``PromptPlugin`` → ``THINK``, ``AdapterPlugin`` → ``PARSE`` + ``DELIVER``).
3. Hints inferred by ``PluginAutoClassifier`` for function plugins.

Explicit stages override type defaults. When they differ, the initializer logs a warning so you can confirm the override is intentional.

## Loading Plugins Automatically

Built-in plugin modules live in `src/plugins`. Place your own plugins inside any directory and load them with `Agent.from_directory(path)` or `Agent.from_package(package)`.

```
agent = Agent.from_directory("./user_plugins")
```

Any import errors are logged and the remaining plugins continue to load.

## Discovering Plugins from `pyproject.toml`

`SystemInitializer` can scan arbitrary directories for `pyproject.toml` files
containing plugin definitions. Add paths to the `plugin_dirs` list in your
configuration:

```yaml
plugin_dirs:
  - ./third_party_plugins
```

Each `pyproject.toml` should define plugins under `[tool.entity.plugins]`:

```toml
[tool.entity.plugins.prompts.example]
class = "my_pkg.example:ExamplePrompt"
dependencies = ["memory"]

[tool.entity.plugins.tools.calc]
class = "my_pkg.calc:CalculatorTool"
```

During initialization the discovered entries are merged into the config and
their dependencies validated automatically.

### External Plugin Repositories

Plugins can live in their own repositories. The
[`entity-debug-plugin`](https://github.com/Ladvien/entity-debug-plugin) example
demonstrates a standalone debug plugin that relies on the local `entity`
package through a path dependency. Point `plugin_dirs` at the repository so the
initializer discovers its `pyproject.toml`:

```yaml
plugin_dirs:
  - ../entity-debug-plugin
```

## Development Steps
1. Create your plugin class and implement `_execute_impl`.
2. Register the plugin with the `Agent` or include it in your YAML under `plugins:`.
   Plugins run sequentially in the exact order listed. There is no priority field.
3. Run `python -m src.entity_config.validator --config your.yaml` to verify configuration.
4. Write unit tests and run `pytest` before committing changes.

## Implementing Storage Backends

Storage resources persist conversation history and other agent data. To add a
new backend, subclass `ResourcePlugin` and implement the `save_history` and
`load_history` methods.

```python
import asyncpg

from pipeline.stages import PipelineStage
from plugins import ResourcePlugin


class MyStorage(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def initialize(self) -> None:
        self.pool = await asyncpg.create_pool(dsn=self.config["dsn"], min_size=1, max_size=5)

    async def save_history(self, conversation_id: str, history):
        async with self.pool.acquire() as conn:
            for entry in history:
                await conn.execute(
                    "INSERT INTO history (id, role, content) VALUES ($1, $2, $3)",
                    conversation_id,
                    entry.role,
                    entry.content,
                )

    async def load_history(self, conversation_id: str):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT role, content FROM history WHERE id=$1", conversation_id)
        return [row["content"] for row in rows]
```

Any plugin can now call `context.get_resource("database")` and use these
methods, enabling a consistent storage interface across resources.



## Example Pipelines

Several example pipelines in the `examples/` directory showcase more advanced patterns.

### StorageResource Composition

`StorageResource` composes `DatabaseResource`, `VectorStoreResource`, and `FileSystemResource` behind one interface for handling files. The pipeline at `examples/pipelines/memory_composition_pipeline.py` demonstrates the same pattern using the unified `Memory` resource. `Memory` persists conversation history and vectors and is configured in [config/dev.yaml](../../config/dev.yaml). Use `StorageResource` when your plugins need to create or read files. With the plugin configured the code looks like:

```python
resources = ResourceContainer()
resources.register("database", DuckDBDatabaseResource, {"path": "./agent.duckdb"})
resources.register("vector_store", PgVectorStore, {"table": "embeddings"})
resources.register("filesystem", LocalFileSystemResource, {"base_path": "./files"})
resources.register("storage", StorageResource, {})
await resources.build_all()
storage = resources.get("storage")
```

`StorageResource` offers the same interface when you only need history and file storage:

```python
resources = ResourceContainer()
resources.register("database", DuckDBDatabaseResource, {"path": "./agent.duckdb"})
resources.register("filesystem", LocalFileSystemResource, {"base_path": "./files"})
resources.register("storage", StorageResource, {})
await resources.build_all()
```
The script at `examples/storage_resource_example.py` demonstrates this setup.

### Vector Memory

`examples/pipelines/vector_memory_pipeline.py` shows a custom `ResourcePlugin` that stores vectors in memory. A prompt plugin retrieves vectors and interacts with the LLM:

```python
class VectorMemoryResource(ResourcePlugin):
    stages = [PipelineStage.PARSE]
    name = "vector_memory"

    def add(self, key: str, vector: List[float]) -> None:
        self.vectors[key] = vector
```

These scripts are great starting points when designing your own plugins.
The `examples/tools/search_weather_example.py` script demonstrates
registering built-in tools directly with an `Agent` and combining their
results.

### Adapter and Failure Examples

The repository also includes short examples for adapter usage and basic
failure handling. See [`examples/servers/cli_adapter.py`](../../examples/servers/cli_adapter.py)
for how to expose an `Agent` through a command line interface. Use `src/cli.py`
to run the agent interactively or over a WebSocket connection:

```bash
poetry run python src/cli.py --config config/dev.yaml
poetry run python src/cli.py serve-websocket --config config/dev.yaml
```

When implementing custom error handling, refer to
[`examples/failure_example.py`](../../examples/failure_example.py),
the failure plugin template at `src/cli/templates/failure.py`,
and the [error handling guide](error_handling.md).

## Troubleshooting Plugins
- **Plugin not executing** – confirm the `stages` list contains the desired pipeline stage.
- **Missing dependency** – ensure the plugin name appears in `plugins.resources` or `plugins.tools`.
- **Runtime errors** – run with `LOG_LEVEL=DEBUG` to see the full traceback.


