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

