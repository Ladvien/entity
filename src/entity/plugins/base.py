from __future__ import annotations

from abc import ABC, abstractmethod
import time
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from entity.resources.logging import LogCategory, LogLevel


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
        """Validate and run the plugin implementation with observability."""
        self._enforce_stage(context)

        logger = getattr(context, "logger", None)
        metrics = getattr(context, "metrics_collector", None)
        start = time.perf_counter()

        if logger is not None:
            await logger.log(
                LogLevel.INFO,
                LogCategory.PLUGIN_LIFECYCLE,
                "Starting plugin execution",
                stage=context.current_stage,
                plugin_name=self.__class__.__name__,
                dependencies=self.dependencies,
            )

        try:
            result = await self._execute_impl(context)
            success = True
            return result
        except Exception as exc:  # pragma: no cover - simple example
            success = False
            if logger is not None:
                await logger.log(
                    LogLevel.ERROR,
                    LogCategory.ERROR,
                    f"Plugin execution failed: {str(exc)}",
                    stage=context.current_stage,
                    plugin_name=self.__class__.__name__,
                    error=str(exc),
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
            if logger is not None and success:
                await logger.log(
                    LogLevel.INFO,
                    LogCategory.PLUGIN_LIFECYCLE,
                    "Plugin execution completed successfully",
                    stage=context.current_stage,
                    plugin_name=self.__class__.__name__,
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
