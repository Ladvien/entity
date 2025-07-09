"""Template for a failure plugin.

Failure plugins run when other plugins raise an error. Integrate the
generated plugin into a workflow as an ``ERROR`` stage handler:

```
workflow = {PipelineStage.ERROR: ["MyFailureHandler"]}
```
"""

from entity.core.plugins import FailurePlugin
from entity.core.stages import PipelineStage


class {class_name}(FailurePlugin):
    """Example failure plugin."""

    stages = [PipelineStage.ERROR]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        context.cache("failure_info", context.get_failure_info())
