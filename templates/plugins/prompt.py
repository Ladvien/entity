"""Template for a prompt plugin.

Prompt plugins drive the conversation. Include the generated class in a
workflow mapping under the ``THINK`` stage:

```
workflow = {PipelineStage.THINK: ["MyPromptPlugin"]}
```
"""

from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class CLASS_NAME(PromptPlugin):
    """Example prompt plugin.

    Replace ``CLASS_NAME`` with your prompt plugin name.
    """

    stages = [PipelineStage.THINK]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        if await context.reflect("answer") is not None:
            context.say(await context.reflect("answer"))
            return

        result = await context.tool_use("some_tool", query=context.message)
        await context.think("answer", result)
        context.say(result)
