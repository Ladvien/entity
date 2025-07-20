from __future__ import annotations

<<<<<<< HEAD
from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage

=======
from typing import Any, TYPE_CHECKING

from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from entity.core.context import PluginContext

>>>>>>> pr-1847

class FailureResponder(PromptPlugin):
    """Respond with the formatted failure message."""

    stages = [PipelineStage.OUTPUT]

<<<<<<< HEAD
    async def _execute_impl(self, context: PluginContext) -> None:
        failure_message: Any = await context.reflect("failure_response")
        if failure_message is not None:
            if hasattr(failure_message, "to_dict"):
                failure_message = failure_message.to_dict()
            context.say(failure_message)
=======
    async def _execute_impl(self, context: "PluginContext") -> None:
        failure_message: Any = await context.reflect("failure_response")
        if failure_message is None:
            return
        if hasattr(failure_message, "to_dict"):
            failure_message = failure_message.to_dict()
        context.say(failure_message)
>>>>>>> pr-1847
