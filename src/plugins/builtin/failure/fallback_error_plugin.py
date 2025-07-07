from __future__ import annotations

"""Fallback error plugin used when no response is produced."""

from pipeline.base_plugins import FailurePlugin
from pipeline.context import PluginContext
from pipeline.errors import create_static_error_response
from pipeline.stages import PipelineStage


class FallbackErrorPlugin(FailurePlugin):
    """Provide a generic error response."""

    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, context: PluginContext) -> None:
        context.set_response(create_static_error_response(context.pipeline_id))
