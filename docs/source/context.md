# Plugin Context

`PluginContext` acts as the gateway between a plugin and the running pipeline. It exposes:

- conversation history and other pipeline state
- registered resources via `get_resource`
- temporary data with `store()`, `load()`, and `has()`
- tool execution through `tool_use()` and `queue_tool_use()`
- helpers for adding conversation entries

Plugins receive this object inside their `_execute_impl` method.

```python
class ExamplePlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        db = context.get_resource("database")
        context.add_conversation_entry("starting", role="system")
        rows = await db.fetch_last(context.user)
```

`PluginContext` includes convenience methods for common operations:

- `say()` to set the pipeline response
- `ask_llm()` to call the configured LLM
- `store()`, `load()`, and `has()` for sharing data between stages
- `tool_use()` to run a tool and wait for the result
- `queue_tool_use()` to defer tool execution until later

```python
class MyPrompt(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        if context.has("summary"):
            context.say(context.load("summary"))
            return

        summary = await context.tool_use("summarize", text=context.message)
        context.store("summary", summary)
        context.queue_tool_use("log_summary", {"text": summary})
        context.say(summary)
```

## Stage Results

Use `store()` to save intermediate data that later stages can retrieve.

```python
context.store("answer", "The Eiffel Tower is in Paris")
if context.has("answer"):
    result = context.load("answer")
```

## Advanced API

Some less common operations are exposed through `context.advanced`.
Use this wrapper when you need direct control over the pipeline state.

```python
async def cleanup(context: PluginContext) -> None:
    context.advanced.replace_conversation_history([])
    await context.advanced._wait_for_tool_result("setup")
```

During stage execution the framework creates a `PluginContext` and passes it to each plugin:

```python
for plugin in stage_plugins:
    plugin_context = PluginContext(state, capabilities)
    await plugin.execute(plugin_context)
```
