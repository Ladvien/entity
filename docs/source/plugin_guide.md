# Writing Plugins

The Entity framework is built around extensible plugins. Plugins run during specific pipeline stages and interact with the system through `PluginContext`.

## Basic Class Plugin

Create a plugin class that inherits from one of the base plugin types and implement `_execute_impl`:

```python
from pipeline.plugins import PromptPlugin
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
from pipeline.plugins import ResourcePlugin
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

Any plugin can now call `context.get_resource("storage")` and use these
methods. Prompt plugins like `ChatHistory` or `MemoryPlugin` work with
PostgreSQL, SQLite, or in-memory backends without code changes.

