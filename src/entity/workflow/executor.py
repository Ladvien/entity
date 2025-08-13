from __future__ import annotations

import uuid
from itertools import count
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from entity.core.error_analysis import error_analyzer
from entity.core.errors import PipelineError, PluginError, error_context_manager
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
    from entity.workflow.workflow import Workflow


class WorkflowExecutor:
    """Run plugins through the standard workflow stages."""

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
        if "memory" not in self.resources:
            from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
            from entity.resources import DatabaseResource, Memory, VectorStoreResource

            self.resources["memory"] = Memory(
                DatabaseResource(DuckDBInfrastructure(":memory:")),
                VectorStoreResource(DuckDBInfrastructure(":memory:")),
            )
        self.workflow = workflow or Workflow()

        self._stage_dependencies: Dict[str, Set[str]] = {
            self.INPUT: set(),
            self.PARSE: {self.INPUT},
            self.THINK: {self.INPUT, self.PARSE},
            self.DO: {self.INPUT, self.PARSE},
            self.REVIEW: {self.INPUT, self.PARSE},
            self.OUTPUT: {self.INPUT},
            self.ERROR: set(),
        }

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
        request_id: Optional[str] = None,
    ) -> str:
        """Run plugins in sequence until an OUTPUT plugin produces a response."""

        if request_id is None:
            request_id = str(uuid.uuid4())

        error_context = error_context_manager.create_context(
            user_id=user_id, stage=self.INPUT, request_id=request_id
        )

        context = PluginContext(self.resources, user_id)
        context.request_id = request_id
        await context.load_state()
        result = message

        try:
            output_configured = bool(self.workflow.plugins_for(self.OUTPUT))
            for loop_count in count():
                context.loop_count = loop_count
                for stage in self._ORDER:
                    error_context.stage = stage
                    error_context_manager.add_execution_context(
                        request_id, "loop_count", loop_count
                    )
                    error_context_manager.add_execution_context(
                        request_id, "stage", stage
                    )

                    result = await self._run_stage(
                        stage, context, result, user_id, request_id
                    )
                    if context.current_stage == self.ERROR:
                        return result
                    if stage == self.OUTPUT and context.response is not None:
                        return context.response
                if not output_configured:
                    break
            await context.flush_state()
            return result
        except PluginError:
            # Re-raise PluginError without wrapping
            raise
        except Exception as exc:
            pipeline_error = error_context_manager.create_pipeline_error(
                stage=getattr(context, "current_stage", "unknown"),
                plugin=None,
                original_error=exc,
                context=error_context,
            )

            error_analyzer.record_error(pipeline_error)

            await context.log(
                LogLevel.ERROR,
                LogCategory.SYSTEM,
                f"Pipeline execution failed: {pipeline_error}",
                exception=str(pipeline_error),
            )
            raise pipeline_error
        finally:
            error_context_manager.cleanup_context(request_id)

    async def _run_stage(
        self,
        stage: str,
        context: PluginContext,
        message: str,
        user_id: str,
        request_id: str,
    ) -> str:
        """Execute all plugins configured for ``stage`` and return the result."""

        context.current_stage = stage
        context.message = message
        result = message

        plugins = self.workflow.plugins_for(stage)

        active_plugins = []
        for plugin in plugins:
            if plugin.should_execute(context):
                active_plugins.append(plugin)
            else:
                plugin_name = plugin.__class__.__name__
                context.skipped_plugins.append(f"{stage}.{plugin_name}")
                self._skip_metrics["plugins_skipped"] += 1

                await context.log(
                    LogLevel.DEBUG,
                    LogCategory.SYSTEM,
                    f"Skipped plugin {plugin_name} in stage {stage}",
                )

        if not active_plugins and self._can_skip_stage(stage, context):
            context.skipped_stages.append(stage)
            self._skip_metrics["stages_skipped"] += 1

            await context.log(
                LogLevel.DEBUG,
                LogCategory.SYSTEM,
                f"Skipped stage {stage} - no active plugins",
            )
            return message

        self._skip_metrics["total_stages_run"] += 1

        for plugin in active_plugins:
            plugin_name = plugin.__class__.__name__
            try:
                error_context_manager.update_plugin_stack(request_id, plugin_name)
                error_context_manager.add_execution_context(
                    request_id, "current_plugin", plugin_name
                )

                self._skip_metrics["total_plugins_run"] += 1
                result = await plugin.execute(context)
            except Exception as exc:
                error_context = error_context_manager.get_context(request_id)
                if error_context:
                    plugin_error = PluginError(
                        plugin_name=plugin_name,
                        stage=stage,
                        context=error_context,
                        original_error=exc.__cause__ or exc,
                        plugin_config=getattr(plugin, "config", {}),
                    )

                    error_analyzer.record_error(plugin_error)

                    await context.log(
                        LogLevel.ERROR,
                        LogCategory.SYSTEM,
                        f"Plugin {plugin_name} failed: {plugin_error}",
                        exception=str(plugin_error),
                    )

                    await self._handle_error(context, plugin_error, user_id, request_id)
                    if context.response is not None:
                        return context.response
                    raise plugin_error
                else:
                    await self._handle_error(
                        context, exc.__cause__ or exc, user_id, request_id
                    )
                    if context.response is not None:
                        return context.response
                    raise

        await context.run_tool_queue()
        await context.flush_state()
        return result

    async def _handle_error(
        self, context: PluginContext, exc: Exception, user_id: str, request_id: str
    ) -> None:
        """Run error stage plugins when a plugin fails with enhanced context."""
        context.current_stage = self.ERROR

        if isinstance(exc, PipelineError):
            context.message = str(exc)
            context.error_context = exc.to_dict()
        else:
            context.message = str(exc)
            context.error_context = {
                "error_type": exc.__class__.__name__,
                "message": str(exc),
                "request_id": request_id,
            }

        error_context_manager.add_execution_context(
            request_id, "error_stage", "error_handling"
        )

        for plugin in self.workflow.plugins_for(self.ERROR):
            try:
                await plugin.execute(context)
            except Exception as error_plugin_exc:
                await context.log(
                    LogLevel.ERROR,
                    LogCategory.SYSTEM,
                    f"Error plugin {plugin.__class__.__name__} failed: {error_plugin_exc}",
                    exception=str(error_plugin_exc),
                )

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
        if stage in {self.INPUT, self.ERROR, self.OUTPUT}:
            return False

        dependencies = self._stage_dependencies.get(stage, set())
        for dep in dependencies:
            if dep in context.skipped_stages:
                return False

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

    def get_error_patterns(self, min_occurrences: int = 1) -> List[Any]:
        """Get error patterns from the error analyzer."""
        return error_analyzer.get_error_patterns(min_occurrences)

    def get_debug_report(self, request_id: str) -> str:
        """Generate debug report for a specific request."""
        return error_analyzer.generate_debug_report(request_id)

    def analyze_recent_errors(self, hours: int = 1) -> Dict[str, Any]:
        """Analyze recent errors for trends."""
        from datetime import timedelta

        return error_analyzer.analyze_recent_errors(timedelta(hours=hours))
