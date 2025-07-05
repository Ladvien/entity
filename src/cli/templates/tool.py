from typing import Any, Dict

from pipeline.base_plugins import ToolPlugin
from pipeline.stages import PipelineStage


class {class_name}(ToolPlugin):
    """Example tool plugin."""

    stages = [PipelineStage.DO]

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return None
