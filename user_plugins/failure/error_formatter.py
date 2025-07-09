from __future__ import annotations

from entity.core.plugins import FailurePlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from entity.core.context import PluginContext
from pipeline.errors import create_error_response, create_static_error_response
from pipeline.stages import PipelineStage


class ErrorFormatter(FailurePlugin):
    """Generate a simple user message from captured failure information."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        info = context.get_failure_info()
        if info is None:
            context.set_response(create_static_error_response(context.pipeline_id))
            return
        context.set_response(create_error_response(context.pipeline_id, info))
