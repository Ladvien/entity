"""Template for failure plugin."""

from pipeline.base_plugins import FailurePlugin
from pipeline.stages import PipelineStage


class {class_name}(FailurePlugin):
    """Example failure plugin."""

    stages = [PipelineStage.ERROR]
    # Execution order follows the YAML list or registration sequence; no priority field

    async def _execute_impl(self, context):
        context.store("failure_info", context.get_failure_info())
