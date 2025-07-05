from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage


class {class_name}(ResourcePlugin):
    """Example resource plugin."""

    stages = [PipelineStage.PARSE]

    @classmethod
    def validate_config(cls, config: dict) -> ValidationResult:
        return ValidationResult.success()

    async def initialize(self) -> None:
        pass

    async def _execute_impl(self, context) -> None:
        return None
