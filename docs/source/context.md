# Plugin Context

`PluginContext` acts as the gateway between a plugin and the running pipeline. It exposes:

- conversation history and other pipeline state
- registered resources via `get_resource`
- tool execution through `execute_tool`
- helpers for adding conversation entries and stage results

Plugins receive this object inside their `_execute_impl` method.

```python
class ExamplePlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        db = context.get_resource("database")
        context.add_conversation_entry("starting", role="system")
        rows = await db.fetch_last(context.user)
```

`SimpleContext` extends `PluginContext` with convenience methods:

- `say()` to set the pipeline response
- `ask_llm()` to call the configured LLM
- `use_tool()` to run a tool and wait for the result

```python
class MyPrompt(PromptPlugin):
    async def _execute_impl(self, context: SimpleContext) -> None:
        reply = await context.ask_llm(context.message)
        context.say(reply)
```

During stage execution the framework creates a `PluginContext` and passes it to each plugin:

```python
for plugin in stage_plugins:
    plugin_context = PluginContext(state, registries)
    await plugin.execute(plugin_context)
```
