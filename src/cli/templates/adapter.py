from pipeline.stages import PipelineStage
from pipeline.user_plugins import AdapterPlugin


class {class_name}(AdapterPlugin):
    """Example adapter plugin."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        pass
