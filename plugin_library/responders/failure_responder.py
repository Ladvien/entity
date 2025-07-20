from __future__ import annotations

<<<<<<< HEAD
from typing import TYPE_CHECKING

from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from entity.core.context import PluginContext


class FailureResponder(PromptPlugin):
    """Emit a final failure message when available."""
=======
from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class FailureResponder(PromptPlugin):
    """Respond with the formatted failure message."""
>>>>>>> pr-1845

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
<<<<<<< HEAD
        failure = await context.reflect("failure_response")
        if failure is None:
            return
        if hasattr(failure, "to_dict"):
            failure = failure.to_dict()
        context.say(failure)
=======
        failure_message: Any = await context.reflect("failure_response")
        if failure_message is not None:
            if hasattr(failure_message, "to_dict"):
                failure_message = failure_message.to_dict()
            context.say(failure_message)
>>>>>>> pr-1845
