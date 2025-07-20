from __future__ import annotations

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class ResponseReviewer(PromptPlugin):
    """Sanitize the final response before delivery."""

    stages = [PipelineStage.REVIEW]

    async def _execute_impl(self, context: PluginContext) -> None:
        if not context.has_response():
            return
        updated = context.response.replace("badword", "***")
        context.update_response(lambda _old: updated)
