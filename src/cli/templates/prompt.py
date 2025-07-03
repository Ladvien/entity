# mypy: ignore-errors

from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class TemplatePrompt(PromptPlugin):
    """Example prompt plugin."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass
