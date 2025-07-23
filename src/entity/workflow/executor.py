from __future__ import annotations

from typing import Any, Iterable

from ..plugins.context import PluginContext


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

    async def run(self, message: str, user_id: str = "default") -> str:
        """Execute configured plugins in order until an OUTPUT plugin calls ``say``."""

        context = PluginContext(self.resources, user_id)
        result = message
        for stage in self._ORDER:
            for plugin_cls in self.workflow.get(stage, []):
                plugin = plugin_cls(self.resources)
                if hasattr(plugin, "context"):
                    plugin.context = context

                context.current_stage = stage
                context.message = result
                if hasattr(plugin, "execute"):
                    result = await plugin.execute(context)
                else:
                    # Fallback for legacy plugins
                    result = await plugin.run(result, user_id)

                if stage == self.OUTPUT and context.response is not None:
                    return context.response
        return result
