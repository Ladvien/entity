# Plugin Development Cheat Sheet

Brief reminders for writing plugins.

## Base Classes
- `ResourcePlugin` – provides infrastructure like databases and LLMs.
- `ToolPlugin` – exposes a callable tool to other plugins.
- `PromptPlugin` – contains reasoning or memory logic.
- `AdapterPlugin` – handles external interfaces such as HTTP or CLI.
- `FailurePlugin` – formats and logs errors.

All plugins declare their `stages` and any `dependencies`.

## Skeleton
```python
from plugins import PromptPlugin
from pipeline.stages import PipelineStage

class ExamplePlugin(PromptPlugin):
    dependencies = ["database", "llm"]
    stages = [PipelineStage.THINK]

    @classmethod
    def validate_config(cls, config):
        return ValidationResult.success()

    async def _execute_impl(self, context):
        # plugin logic here
        pass
```

Register plugins through `Agent.add_plugin()` or in a YAML configuration file.
Plugins run sequentially in the order listed under each stage; there is no priority.
