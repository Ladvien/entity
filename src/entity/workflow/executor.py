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
    ERROR = "error"

    _ORDER = [INPUT, PARSE, THINK, DO, REVIEW, OUTPUT]
    _STAGES = _ORDER + [ERROR]

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
                try:
                    if hasattr(plugin, "execute"):
                        result = await plugin.execute(context)
                    else:
                        # Fallback for legacy plugins
                        result = await plugin.run(result, user_id)
                except Exception as exc:  # pragma: no cover - runtime errors
                    await self._handle_error(context, exc, user_id)
                    raise

            await context.run_tool_queue()

            if stage == self.OUTPUT and context.response is not None:
                return context.response
        return result

    async def _handle_error(
        self, context: PluginContext, exc: Exception, user_id: str
    ) -> None:
        """Run error stage plugins when a plugin fails."""
        context.current_stage = self.ERROR
        context.message = str(exc)
        for plugin_cls in self.workflow.get(self.ERROR, []):
            plugin = plugin_cls(self.resources)
            if hasattr(plugin, "context"):
                plugin.context = context
            if hasattr(plugin, "execute"):
                await plugin.execute(context)
            else:  # pragma: no cover - legacy hook
                await plugin.run(str(exc), user_id)
