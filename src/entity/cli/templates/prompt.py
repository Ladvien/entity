"""Template for a prompt plugin.

Prompt plugins drive the conversation. Include the generated class in a
workflow mapping under the ``THINK`` stage:

```
workflow = {PipelineStage.THINK: ["MyPromptPlugin"]}
```

THINK-stage plugins collect intermediate results with :meth:`context.think`.
An OUTPUT-stage plugin should later read those results and call
:meth:`context.say` to generate the final response.
"""

from entity.core.plugins import PromptPlugin
from entity.core.stages import PipelineStage


class CLASS_NAME(PromptPlugin):
    """Example prompt plugin.

    Replace ``CLASS_NAME`` with your prompt plugin name.
    """

    stages = [PipelineStage.THINK]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        cached_answer = await context.reflect("answer")
        if cached_answer is not None:
            await context.think("answer", cached_answer)
            return

        result = await context.tool_use("some_tool", query=context.message)
        await context.think("answer", result)
