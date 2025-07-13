"""Template for an adapter plugin.

Adapters connect pipeline output to the outside world. Add the generated
plugin to a workflow so it runs in the ``OUTPUT`` stage:

```
workflow = {PipelineStage.OUTPUT: ["MyAdapter"]}
```
"""

from entity.core.plugins import AdapterPlugin
from entity.core.stages import PipelineStage


class CLASS_NAME(AdapterPlugin):
    """Example adapter plugin.

    Replace ``CLASS_NAME`` with your adapter class name.
    """

    stages = [PipelineStage.OUTPUT]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        if await context.reflect("response") is not None:
            await context.advanced.queue_tool_use(
                "send", {"text": await context.reflect("response")}
            )
