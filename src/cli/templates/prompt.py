"""Template for prompt plugin."""

from pipeline.base_plugins import PromptPlugin
from pipeline.stages import PipelineStage


class {class_name}(PromptPlugin):
    """Example prompt plugin."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass
