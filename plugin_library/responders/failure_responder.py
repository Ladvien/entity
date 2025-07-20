from __future__ import annotations

<<<<<<< HEAD
from entity.plugins.base import PromptPlugin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from entity.core.context import PluginContext

=======
from typing import Any

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
>>>>>>> pr-1843
from entity.core.stages import PipelineStage


class FailureResponder(PromptPlugin):
<<<<<<< HEAD
    """Emit a final failure message when available."""
=======
    """Respond with the formatted failure message."""
>>>>>>> pr-1843

    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
<<<<<<< HEAD
        failure = await context.reflect("failure_response")
        if failure is None:
            return
        if hasattr(failure, "to_dict"):
            failure = failure.to_dict()
        await context.say(failure)
=======
        message: Any = await context.reflect("failure_response")
        if message is not None:
            if hasattr(message, "to_dict"):
                message = message.to_dict()
            context.say(message)
>>>>>>> pr-1843
