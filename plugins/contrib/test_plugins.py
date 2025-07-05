from __future__ import annotations

from pipeline import PipelineStage, PromptPlugin, ToolPlugin, ValidationResult
from pipeline.context import PluginContext


class ReloadPlugin(PromptPlugin):
    """Simple prompt plugin used for CLI reload tests."""

    stages = [PipelineStage.THINK]
    name = "reload"

    async def _execute_impl(self, context: PluginContext) -> None:
        """No-op plugin for CLI reload tests."""
        return None

    @classmethod
    def validate_config(cls, config: dict) -> ValidationResult:
        if "value" not in config:
            return ValidationResult.error_result("missing value")
        return ValidationResult.success_result()


class ReloadTool(ToolPlugin):
    """Echo tool for CLI reload tests."""

    name = "echo"

    async def execute_function(self, params: dict) -> str:
        """Return the provided text parameter."""
        return str(params.get("text", ""))
