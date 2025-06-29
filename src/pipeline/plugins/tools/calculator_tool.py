from __future__ import annotations

from typing import Any, Dict

from pipeline.plugins import ToolPlugin
from pipeline.stages import PipelineStage


class CalculatorTool(ToolPlugin):
    """Evaluate simple math expressions using Python's eval."""

    stages = [PipelineStage.DO]

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        expression = params.get("expression")
        if not expression:
            raise ValueError("'expression' parameter is required")
        allowed_names: Dict[str, Dict[str, Any]] = {"__builtins__": {}}
        try:
            result = eval(str(expression), allowed_names, {})
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")
        return result
