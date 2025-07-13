"""Template for a resource plugin.

Resources prepare data for other plugins. Add the generated resource to a
workflow mapping so it executes in the ``PARSE`` stage:

```
workflow = {PipelineStage.PARSE: ["MyResource"]}
```
"""

from entity.core.plugins import ResourcePlugin, ValidationResult
from entity.core.stages import PipelineStage


class CLASS_NAME(ResourcePlugin):
    """Example resource plugin.

    Replace ``CLASS_NAME`` with your resource plugin name.
    """

    stages = [PipelineStage.PARSE]
    # List position controls execution order and SystemInitializer preserves it.

    @classmethod
    def validate_config(cls, config: dict) -> ValidationResult:
        return ValidationResult.success_result()

    async def initialize(self) -> None:
        pass

    async def _execute_impl(self, context) -> None:
        context.advanced.queue_tool_use("refresh", {})
