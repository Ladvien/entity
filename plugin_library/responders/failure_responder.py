from __future__ import annotations

from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class FailureResponder(PromptPlugin):
    """Respond with the formatted failure message."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        failure_message: Any = await context.reflect("failure_response")
        if failure_message is not None:
            if hasattr(failure_message, "to_dict"):
                failure_message = failure_message.to_dict()
            context.say(failure_message)
