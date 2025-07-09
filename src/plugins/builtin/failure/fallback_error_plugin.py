from __future__ import annotations

"""Fallback error plugin used when no response is produced."""

from entity.core.plugins import FailurePlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from pipeline.context import PluginContext
from pipeline.errors import create_static_error_response
from pipeline.stages import PipelineStage


class FallbackErrorPlugin(FailurePlugin):
    """Provide a generic error response."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        """Provide a static fallback response."""

        context.set_response(
            create_static_error_response(context.pipeline_id).to_dict()
        )
