from __future__ import annotations

from abc import ABC, abstractmethod
import time
import traceback
from typing import Any, Dict

from pydantic import BaseModel, ValidationError
from entity.resources.logging import LogLevel, LogCategory


class Plugin(ABC):
    """Base class for all plugins."""

    class ConfigModel(BaseModel):
        """Default empty configuration."""

        class Config:  # pragma: no cover - simple pydantic setup
            extra = "forbid"

    stage: str | None = None
    supported_stages: list[str] = []
    dependencies: list[str] = []

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Instantiate the plugin and run all startup validations."""
        self.resources = resources
        # Fail fast on misconfigured options
        self.config = self.validate_config(config or {})
        # Ensure required resources are available before execution starts
        self._validate_dependencies()

    # TODO: Remove unnecessary comments, they are self-explanatory
    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> ConfigModel:
        """Validate ``config`` using ``ConfigModel`` and return the model."""
        try:
            return cls.ConfigModel(**config)
        except ValidationError as exc:  # pragma: no cover - simple conversion
            raise ValueError(
                f"Invalid configuration for {cls.__name__}: {exc}"
            ) from exc

    @classmethod
    def validate_workflow(cls, stage: str) -> None:
        """Validate that ``cls`` can run in ``stage`` before workflow execution."""
        from entity.workflow.workflow import WorkflowConfigError

        if cls.supported_stages and stage not in cls.supported_stages:
            allowed = ", ".join(cls.supported_stages)
            raise WorkflowConfigError(
                f"{cls.__name__} cannot run in stage '{stage}'. "
                f"Supported stages: {allowed}"
            )
        if cls.stage and cls.stage != stage:
            raise WorkflowConfigError(
                f"{cls.__name__} is fixed to stage '{cls.stage}' and cannot "
                f"be scheduled for '{stage}'"
            )

    async def execute(self, context: Any) -> Any:
        """Run the plugin with automatic structured logging."""
        self._enforce_stage(context)

        context._current_plugin_name = self.__class__.__name__
        metrics = getattr(context, "metrics_collector", None)
        start = time.perf_counter()

        await context.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Starting plugin execution",
            plugin_class=self.__class__.__name__,
            stage=context.current_stage,
            dependencies=self.dependencies,
        )

        try:
            result = await self._execute_with_logging(context)
            success = True
            await context.log(
                LogLevel.INFO,
                LogCategory.PLUGIN_LIFECYCLE,
                "Plugin execution completed successfully",
                duration_ms=(time.perf_counter() - start) * 1000,
                result_type=type(result).__name__,
            )
            return result
        except Exception as exc:
            success = False
            await context.log(
                LogLevel.ERROR,
                LogCategory.ERROR,
                f"Plugin execution failed: {str(exc)}",
                exception_type=exc.__class__.__name__,
                duration_ms=(time.perf_counter() - start) * 1000,
                traceback=traceback.format_exc(),
            )
            raise RuntimeError(
                f"{self.__class__.__name__} failed during execution"
            ) from exc
        finally:
            if metrics is not None:
                await metrics.record_plugin_execution(
                    plugin_name=self.__class__.__name__,
                    stage=context.current_stage,
                    duration_ms=(time.perf_counter() - start) * 1000,
                    success=success,
                )

    def _enforce_stage(self, context: Any) -> None:
        current = getattr(context, "current_stage", None)
        expected = self.stage
        if expected and current != expected:
            raise RuntimeError(
                f"{self.__class__.__name__} expected stage '{expected}' but "
                f"was scheduled for '{current}'"
            )
        if self.supported_stages and current not in self.supported_stages:
            allowed = ", ".join(self.supported_stages)
            raise RuntimeError(
                f"{self.__class__.__name__} does not support stage '{current}'. "
                f"Supported stages: {allowed}"
            )

    def _validate_dependencies(self) -> None:
        missing = [dep for dep in self.dependencies if dep not in self.resources]
        if missing:
            needed = ", ".join(missing)
            raise RuntimeError(
                f"{self.__class__.__name__} missing required resources: {needed}"
            )

    @abstractmethod
    async def _execute_impl(self, context: Any) -> Any:
        """Plugin-specific execution logic."""
        raise NotImplementedError

    async def _execute_with_logging(self, context: Any) -> Any:
        """Wrap ``_execute_impl`` with logging for context operations."""

        original_get_resource = context.get_resource
        original_remember = context.remember
        original_recall = context.recall
        original_tool_use = context.tool_use

        async def logged_get_resource(name: str):
            await context.log(
                LogLevel.DEBUG,
                LogCategory.RESOURCE_ACCESS,
                f"Accessing resource: {name}",
            )
            return original_get_resource(name)

        async def logged_remember(key: str, value: Any):
            await context.log(
                LogLevel.DEBUG,
                LogCategory.MEMORY_OPERATION,
                f"Storing memory key: {key}",
                value_type=type(value).__name__,
            )
            return await original_remember(key, value)

        async def logged_recall(key: str, default: Any = None):
            result = await original_recall(key, default)
            await context.log(
                LogLevel.DEBUG,
                LogCategory.MEMORY_OPERATION,
                f"Retrieved memory key: {key}",
                found=result is not None,
                value_type=type(result).__name__ if result is not None else None,
            )
            return result

        async def logged_tool_use(name: str, **kwargs):
            await context.log(
                LogLevel.INFO,
                LogCategory.TOOL_USAGE,
                f"Executing tool: {name}",
                tool_args=list(kwargs.keys()),
            )
            start = time.perf_counter()
            try:
                result = await original_tool_use(name, **kwargs)
                await context.log(
                    LogLevel.INFO,
                    LogCategory.TOOL_USAGE,
                    f"Tool execution completed: {name}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                    success=True,
                )
                return result
            except Exception as exc:
                await context.log(
                    LogLevel.ERROR,
                    LogCategory.TOOL_USAGE,
                    f"Tool execution failed: {name}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                    success=False,
                    error=str(exc),
                )
                raise

        context.get_resource = logged_get_resource
        context.remember = logged_remember
        context.recall = logged_recall
        context.tool_use = logged_tool_use

        try:
            return await self._execute_impl(context)
        finally:
            context.get_resource = original_get_resource
            context.remember = original_remember
            context.recall = original_recall
            context.tool_use = original_tool_use
