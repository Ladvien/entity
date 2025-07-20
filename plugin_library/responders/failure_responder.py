from __future__ import annotations

from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class FailureResponder(PromptPlugin):
    """Respond with the formatted failure message."""

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        message: Any = await context.reflect("failure_response")
        if message is not None:
            if hasattr(message, "to_dict"):
                message = message.to_dict()
            context.say(message)
