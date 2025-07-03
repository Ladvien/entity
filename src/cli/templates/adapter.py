# mypy: ignore-errors

from pipeline.plugins import AdapterPlugin
from pipeline.stages import PipelineStage


class TemplateAdapter(AdapterPlugin):
    """Example adapter plugin."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        pass
