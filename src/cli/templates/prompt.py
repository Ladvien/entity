from pipeline.stages import PipelineStage
from pipeline.user_plugins import PromptPlugin


class {class_name}(PromptPlugin):
    """Example prompt plugin."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass
