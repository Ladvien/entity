```{include} ../../README.md
:relative-images:
:start-after: <!-- start quick_start -->
:end-before: <!-- end quick_start -->
```

### CLI Usage
Run an agent from a YAML configuration file:

```bash
python src/cli.py --config config.yml
```

### Using the SearchTool
Register `SearchTool` and call it from your plugin:

```python
from entity.tools import SearchTool

agent.tool_registry.add("search", SearchTool())

@agent.plugin
async def lookup(context):
    return await context.use_tool("search", query="Entity Pipeline")
```
