# Writing Plugins

The Entity framework is built around extensible plugins. Plugins run during specific pipeline stages and interact with the system through `PluginContext`.

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
from entity import Agent

agent = Agent()
agent.add_plugin(HelloPlugin({}))
```

## Function Plugin

You can also register an async function using the `@agent.plugin` decorator. The framework will automatically classify it and wrap it in a plugin object.

```python
agent = Agent()

@agent.plugin
async def weather_plugin(ctx):
    return await ctx.use_tool("weather", city="London")
```

## Loading Plugins Automatically

Place plugin modules inside a directory and load them with `Agent.from_directory(path)` or `Agent.from_package(package)`.

```
agent = Agent.from_directory("./plugins")
```

Any import errors are logged and the remaining plugins continue to load.

## Implementing Storage Backends

Storage resources persist conversation history and other agent data. To add a
new backend, subclass `ResourcePlugin` and implement the `save_history` and
`load_history` methods.

```python
import asyncpg
from plugins import ResourcePlugin
from pipeline.stages import PipelineStage


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

`StorageResource` composes `DatabaseResource`, `VectorStoreResource`, and `FileSystemResource` behind one interface. The pipeline at `examples/pipelines/memory_composition_pipeline.py` demonstrates the same pattern using the older `MemoryResource`. `MemoryResource` remains the framework's default ephemeral memory, configured in [config/dev.yaml](../../config/dev.yaml). For persistent deployments, prefer `StorageResource` so history, vectors, and files survive restarts. With the new plugin the code looks like:

```python
storage = StorageResource(
    database=SQLiteDatabaseResource({"path": "./agent.db"}),
    vector_store=PgVectorStore({"table": "embeddings"}),
    filesystem=LocalFileSystemResource({"base_path": "./files"}),
)
```

`StorageResource` offers the same interface when you only need history and file storage:

```python
storage = StorageResource(
    database=SQLiteDatabaseResource({"path": "./agent.db"}),
    filesystem=LocalFileSystemResource({"base_path": "./files"}),
)
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
python src/cli.py --config config/dev.yaml
python src/cli.py serve-websocket --config config/dev.yaml
```

When implementing custom error handling, refer to
[`examples/failure_example.py`](../../examples/failure_example.py) and the
failure plugin template at `src/cli/templates/failure.py`.
