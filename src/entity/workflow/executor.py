from __future__ import annotations

from typing import Any, Iterable


class WorkflowContext:
    """Simple context passed to plugins during execution."""

    def __init__(self) -> None:
        self._response: str | None = None

    def say(self, message: str) -> None:
        """Store the final response and mark workflow as complete."""

        self._response = message

    @property
    def response(self) -> str | None:  # noqa: D401
        """Return the response set by :py:meth:`say`."""
        return self._response


class WorkflowExecutor:
    """Run plugins through the standard workflow stages."""

    INPUT = "input"
    PARSE = "parse"
    THINK = "think"
    DO = "do"
    REVIEW = "review"
    OUTPUT = "output"

    _ORDER = [INPUT, PARSE, THINK, DO, REVIEW, OUTPUT]

    def __init__(
        self,
        resources: dict[str, Any],
        workflow: dict[str, Iterable[type]] | None = None,
    ) -> None:
        self.resources = resources
        self.workflow = {
            stage: list(plugins) for stage, plugins in (workflow or {}).items()
        }
        self.context = WorkflowContext()

    async def run(self, message: str, user_id: str = "default") -> str:
        """Execute configured plugins in order until an OUTPUT plugin calls ``say``."""

        result = message
        for stage in self._ORDER:
            for plugin_cls in self.workflow.get(stage, []):
                plugin = plugin_cls(self.resources)
                if hasattr(plugin, "context"):
                    plugin.context = self.context
                result = await plugin.run(result, user_id)

                if stage == self.OUTPUT and self.context.response is not None:
                    return self.context.response
        return result
