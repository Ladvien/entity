"""Template for a failure plugin.

Failure plugins run when other plugins raise an error. Integrate the
generated plugin into a workflow as an ``ERROR`` stage handler:

```
workflow = {PipelineStage.ERROR: ["MyFailureHandler"]}
```
"""

from entity.plugins.base import FailurePlugin
from entity.core.stages import PipelineStage


class CLASS_NAME(FailurePlugin):
    """Example failure plugin.

    Replace ``CLASS_NAME`` with your failure handler name.
    """

    stages = [PipelineStage.ERROR]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        await context.think("failure_info", context.failure_info)
