# Plugin Development

Plugins provide all extendable behavior in the framework. They are grouped by
function and registered through configuration or the `Agent` API.

## Naming Conventions
- Modules live under the `plugins` package
- Class names end with `Plugin`, e.g. `WeatherToolPlugin`
- Each resource exposes one canonical registry name
- Keep names short and descriptive

## Basic Pattern
```python
from plugins import PromptPlugin
from pipeline.stages import PipelineStage

class HelloPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_response("Hello")
```

Plugins may declare dependencies via the `dependencies` list and must specify the
pipeline stages they run in. See `plugin_guide.md` for in‑depth examples.
