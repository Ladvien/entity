"""Template for failure plugin."""

from entity.core.plugins import FailurePlugin
from entity.core.stages import PipelineStage


class {class_name}(FailurePlugin):
    """Example failure plugin."""

    stages = [PipelineStage.ERROR]
    # List position controls execution order and SystemInitializer preserves it.

    async def _execute_impl(self, context):
        context.store("failure_info", context.get_failure_info())
