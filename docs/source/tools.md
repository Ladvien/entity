# Tool Discovery

`ToolRegistry` now exposes a lightweight `query()` method for discovering
available tools. Plugins pass a filter function that receives the tool name and
instance. The registry returns a dictionary of matching entries.

Example:

```python
# Return tools with names starting with "search".
search_tools = registry.tools.query(lambda n, _: n.startswith("search"))
```

Filters let prompts or other tools fetch just the plugins they care about
without scanning the entire registry.
