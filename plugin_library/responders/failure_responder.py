from __future__ import annotations

from typing import TYPE_CHECKING

from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from entity.core.context import PluginContext


class FailureResponder(PromptPlugin):
    """Emit a final failure message when available."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        failure = await context.reflect("failure_response")
        if failure is None:
            return
        if hasattr(failure, "to_dict"):
            failure = failure.to_dict()
        context.say(failure)
