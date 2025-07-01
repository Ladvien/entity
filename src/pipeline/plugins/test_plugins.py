from __future__ import annotations

from pipeline import PipelineStage, PromptPlugin, ToolPlugin, ValidationResult


class ReloadPlugin(PromptPlugin):
    """Simple prompt plugin used for CLI reload tests."""

    stages = [PipelineStage.THINK]
    name = "reload"

    async def _execute_impl(self, context):
        # Test plugin does nothing during execution
        return None

    @classmethod
    def validate_config(cls, config):
        if "value" not in config:
            return ValidationResult.error_result("missing value")
        return ValidationResult.success_result()


class ReloadTool(ToolPlugin):
    """Echo tool for CLI reload tests."""

    name = "echo"

    async def execute_function(self, params):
        return params.get("text", "")
