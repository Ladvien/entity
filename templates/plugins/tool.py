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


class {class_name}(ToolPlugin):
    """Example tool plugin."""

    stages = [PipelineStage.DO]
    # List position controls execution order and SystemInitializer preserves it.

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return None
