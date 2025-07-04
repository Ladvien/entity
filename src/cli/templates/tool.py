from typing import Any, Dict

from pipeline.stages import PipelineStage
from pipeline.user_plugins import ToolPlugin


class {class_name}(ToolPlugin):
    """Example tool plugin."""

    stages = [PipelineStage.DO]

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return None
