from pipeline.plugins import FailurePlugin
from pipeline.stages import PipelineStage


class {class_name}(FailurePlugin):
    """Example failure plugin."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        pass
