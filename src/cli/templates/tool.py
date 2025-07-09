"""Template for tool plugin."""

from typing import Any, Dict

from pipeline.base_plugins import ToolPlugin
from pipeline.stages import PipelineStage


class {class_name}(ToolPlugin):
    """Example tool plugin."""

    stages = [PipelineStage.DO]
    # Execution order follows the YAML list or registration sequence; no priority field

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return None
