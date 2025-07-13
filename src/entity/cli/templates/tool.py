"""Template for a tool plugin.

Tool plugins expose functions that other plugins can call. Register the
generated tool in a workflow under the ``DO`` stage:

```
workflow = {PipelineStage.DO: ["MyTool"]}
```
"""

from typing import Any, Dict

from entity.core.plugins import ToolPlugin
from entity.core.stages import PipelineStage


class CLASS_NAME(ToolPlugin):
    """Example tool plugin.

    Replace ``CLASS_NAME`` with your tool plugin name.
    """

    stages = [PipelineStage.DO]
    intents: list[str] = []
    # List position controls execution order and SystemInitializer preserves it.

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return None
