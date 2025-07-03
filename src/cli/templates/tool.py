from typing import Any, Dict

from pipeline.plugins import ToolPlugin
from pipeline.stages import PipelineStage

# mypy: ignore-errors



class TemplateTool(ToolPlugin):
    """Example tool plugin."""

    stages = [PipelineStage.DO]

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return None
