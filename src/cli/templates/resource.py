from pipeline.stages import PipelineStage
from pipeline.user_plugins import ResourcePlugin, ValidationResult


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
