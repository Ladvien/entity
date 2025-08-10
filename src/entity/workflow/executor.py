from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING, Any, Dict, Set

from entity.plugins.context import PluginContext
from entity.resources.logging import LogCategory, LogLevel, RichConsoleLoggingResource
from entity.workflow.stages import (
    ALL_STAGES,
    DO,
    ERROR,
    INPUT,
    OUTPUT,
    PARSE,
    REVIEW,
    STAGE_ORDER,
    THINK,
)

if TYPE_CHECKING:
    from entity.workflow.workflow import Workflow
else:
    # Import for runtime to avoid NameError
    from entity.workflow.workflow import Workflow


class WorkflowExecutor:
    """Run plugins through the standard workflow stages."""

    # Stage constants for backward compatibility
    INPUT = INPUT
    PARSE = PARSE
    THINK = THINK
    DO = DO
    REVIEW = REVIEW
    OUTPUT = OUTPUT
    ERROR = ERROR

    _ORDER = STAGE_ORDER
    _STAGES = ALL_STAGES

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

        # Track stage dependencies - stages that must run even if no plugins
        self._stage_dependencies: Dict[str, Set[str]] = {
            self.INPUT: set(),
            self.PARSE: {self.INPUT},
            self.THINK: {self.INPUT, self.PARSE},
            self.DO: {self.INPUT, self.PARSE},
            self.REVIEW: {self.INPUT, self.PARSE},
            self.OUTPUT: {self.INPUT},
            self.ERROR: set(),  # ERROR can always run
        }

        # Pipeline optimization metrics
        self._skip_metrics: Dict[str, int] = {
            "stages_skipped": 0,
            "plugins_skipped": 0,
            "total_stages_run": 0,
            "total_plugins_run": 0,
        }

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

        # Get plugins for this stage
        plugins = self.workflow.plugins_for(stage)

        # Filter plugins that should execute
        active_plugins = []
        for plugin in plugins:
            if plugin.should_execute(context):
                active_plugins.append(plugin)
            else:
                # Track skipped plugin
                plugin_name = plugin.__class__.__name__
                context.skipped_plugins.append(f"{stage}.{plugin_name}")
                self._skip_metrics["plugins_skipped"] += 1

                # Log the skip
                await context.log(
                    LogLevel.DEBUG,
                    LogCategory.SYSTEM,
                    f"Skipped plugin {plugin_name} in stage {stage}",
                )

        # Check if we can skip the entire stage
        if not active_plugins and self._can_skip_stage(stage, context):
            context.skipped_stages.append(stage)
            self._skip_metrics["stages_skipped"] += 1

            await context.log(
                LogLevel.DEBUG,
                LogCategory.SYSTEM,
                f"Skipped stage {stage} - no active plugins",
            )
            return message

        # Track that we're running this stage
        self._skip_metrics["total_stages_run"] += 1

        # Execute active plugins
        for plugin in active_plugins:
            try:
                self._skip_metrics["total_plugins_run"] += 1
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

    def _can_skip_stage(self, stage: str, context: PluginContext) -> bool:
        """Determine if a stage can be skipped based on dependencies.

        Args:
            stage: The stage to check
            context: The current plugin context

        Returns:
            True if the stage can be skipped, False otherwise
        """
        # Never skip INPUT, ERROR or OUTPUT stages
        if stage in {self.INPUT, self.ERROR, self.OUTPUT}:
            return False

        # Check if any required dependencies were skipped
        dependencies = self._stage_dependencies.get(stage, set())
        for dep in dependencies:
            if dep in context.skipped_stages:
                # A required dependency was skipped, so we can't skip this stage
                return False

        # Stage can be skipped
        return True

    def get_skip_metrics(self) -> Dict[str, int]:
        """Get pipeline optimization metrics.

        Returns:
            Dictionary containing skip metrics
        """
        return self._skip_metrics.copy()

    def reset_skip_metrics(self) -> None:
        """Reset skip metrics to zero."""
        self._skip_metrics = {
            "stages_skipped": 0,
            "plugins_skipped": 0,
            "total_stages_run": 0,
            "total_plugins_run": 0,
        }
