from __future__ import annotations

from pipeline.base_plugins import FailurePlugin
from pipeline.context import PluginContext
from pipeline.errors import create_error_response, create_static_error_response
from pipeline.stages import PipelineStage


class DefaultResponder(FailurePlugin):
    """Return a standardized error message when failures occur."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        info = context.get_failure_info()
        if info is None:
            context.set_response(create_static_error_response(context.pipeline_id))
        else:
            context.set_response(create_error_response(context.pipeline_id, info))
