from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING, Any

from entity.plugins.context import PluginContext
from entity.resources.logging import RichConsoleLoggingResource

if TYPE_CHECKING:
    from entity.workflow.workflow import Workflow


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
        workflow: "Workflow" | None = None,
    ) -> None:
        self.resources = dict(resources)
        self.resources.setdefault("logging", RichConsoleLoggingResource())
        # Ensure memory is always available, even if in-memory for tests
        if "memory" not in self.resources:
            from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
            from entity.resources import DatabaseResource, Memory, VectorStoreResource

            self.resources["memory"] = Memory(
                DatabaseResource(DuckDBInfrastructure(":memory:")),
                VectorStoreResource(DuckDBInfrastructure(":memory:")),
            )
        self.workflow = workflow or Workflow()

    async def execute(
        self,
        message: str,
        user_id: str = "default",
    ) -> str:
        """Run plugins in sequence until an OUTPUT plugin produces a response."""

        context = PluginContext(self.resources, user_id)
        await context.load_state()
        result = message

        output_configured = bool(self.workflow.plugins_for(self.OUTPUT))
        for loop_count in count():
            context.loop_count = loop_count
            for stage in self._ORDER:
                result = await self._run_stage(stage, context, result, user_id)
                if context.current_stage == self.ERROR:
                    return result
                if stage == self.OUTPUT and context.response is not None:
                    return context.response
            if not output_configured:
                break
        await context.flush_state()
        return result

    async def _run_stage(
        self,
        stage: str,
        context: PluginContext,
        message: str,
        user_id: str,
    ) -> str:
        """Execute all plugins configured for ``stage`` and return the result."""

        context.current_stage = stage
        context.message = message
        result = message

        for plugin in self.workflow.plugins_for(stage):
            try:
                result = await plugin.execute(context)
            except Exception as exc:
                await self._handle_error(context, exc.__cause__ or exc, user_id)
                if context.response is not None:
                    return context.response
                raise

        await context.run_tool_queue()
        await context.flush_state()
        return result

    async def _handle_error(
        self, context: PluginContext, exc: Exception, user_id: str
    ) -> None:
        """Run error stage plugins when a plugin fails."""
        context.current_stage = self.ERROR
        context.message = str(exc)
        for plugin in self.workflow.plugins_for(self.ERROR):
            await plugin.execute(context)
        await context.run_tool_queue()
        await context.flush_state()
