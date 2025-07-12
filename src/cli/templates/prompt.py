"""Template for a prompt plugin.

Prompt plugins drive the conversation. Include the generated class in a
workflow mapping under the ``THINK`` stage:

```
workflow = {PipelineStage.THINK: ["MyPromptPlugin"]}
```
"""

from entity.core.plugins import PromptPlugin
from entity.core.stages import PipelineStage


class {class_name}(PromptPlugin):
    """Example prompt plugin."""

    stages = [PipelineStage.THINK]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        existing = await context.reflect("answer")
        if existing is not None:
            context.say(existing)
            return

        result = await context.tool_use("some_tool", query=context.message)
        await context.think("answer", result)
        context.say(result)
