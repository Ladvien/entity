from pipeline.stages import PipelineStage
from pipeline.user_plugins import FailurePlugin


class {class_name}(FailurePlugin):
    """Example failure plugin."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context):
        pass
