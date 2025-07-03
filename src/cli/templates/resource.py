# mypy: ignore-errors

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage


class TemplateResource(ResourcePlugin):
    """Example resource plugin."""

    stages = [PipelineStage.PARSE]

    @classmethod
    def validate_config(cls, config: dict) -> ValidationResult:
        return ValidationResult.success()

    async def initialize(self) -> None:
        pass

    async def _execute_impl(self, context) -> None:
        return None
