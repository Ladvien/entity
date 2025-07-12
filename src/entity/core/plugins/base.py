"""Core plugin wrappers for the Entity framework.

These classes mirror the minimal architecture described in
``architecture/general.md`` and avoid importing ``entity.core.plugins``.
They offer a small, easy to understand surface for plugin authors.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List

from entity.utils.logging import get_logger
from entity.pipeline.utils import _normalize_stages

from ..stages import PipelineStage


def _ensure_metrics_dependency(cls: type) -> None:
    if cls.__name__ == "MetricsCollectorResource":
        return
    deps = list(getattr(cls, "dependencies", []))
    if "metrics_collector" not in deps:
        deps.append("metrics_collector")
    cls.dependencies = deps


def _ensure_logging_dependency(cls: type) -> None:
    if cls.__name__ == "LoggingResource":
        return
    deps = list(getattr(cls, "dependencies", []))
    if "logging" not in deps:
        deps.append("logging")
    cls.dependencies = deps


class ToolExecutionError(Exception):
    """Raised when a tool fails during execution."""


class BasePlugin:
    """Lightweight plugin foundation."""

    stages: List[PipelineStage]
    dependencies: List[str] = ["metrics_collector", "logging"]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _ensure_metrics_dependency(cls)
        _ensure_logging_dependency(cls)

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self._config_history: list[Dict[str, Any]] = [self.config.copy()]
        self.config_version: int = 1
        self.metrics_collector = None  # injected by container
        self.logging = None  # injected by container

    # -----------------------------------------------------
    def supports_runtime_reconfiguration(self) -> bool:
        """Return ``True`` if the plugin can be reconfigured without restart."""

        return True

    async def rollback_config(self, version: int) -> None:
        """Revert to the specified configuration version."""

        if version < 1 or version > len(self._config_history):
            raise ValueError("invalid version")
        self.config = self._config_history[version - 1].copy()
        self.config_version = version
        self._config_history = self._config_history[:version]

    async def validate_runtime(self) -> "ValidationResult":
        """Validate the runtime environment for the plugin."""

        return ValidationResult.success_result()

    async def call_llm(self, context: Any, prompt: str, purpose: str = "") -> Any:
        start = time.perf_counter()
        success = True
        response = None
        try:
            response = await context.call_llm(context, prompt, purpose=purpose)
            return response
        except Exception:
            success = False
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            self.logger.info(
                "LLM call completed",
                extra={
                    "plugin": self.__class__.__name__,
                    "stage": str(getattr(context, "current_stage", "")),
                    "purpose": purpose,
                    "prompt_length": len(prompt),
                    "response_length": (
                        len(getattr(response, "content", "")) if response else 0
                    ),
                    "pipeline_id": getattr(context, "pipeline_id", ""),
                    "duration": duration,
                },
            )
            metrics = getattr(self, "metrics_collector", None)
            if metrics is not None:
                await metrics.record_resource_operation(
                    pipeline_id=getattr(context, "pipeline_id", ""),
                    resource_name="llm",
                    operation="generate",
                    duration_ms=duration,
                    success=success,
                    metadata={"purpose": purpose, "prompt_length": len(prompt)},
                )

    async def _execute_impl(self, context: Any) -> Any:
        """Execute plugin logic in the pipeline."""
        raise NotImplementedError


class Plugin(BasePlugin):
    """Base plugin implementation with default behaviors."""

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> "ValidationResult":
        """Validate ``config`` and return ``ValidationResult``."""

        return ValidationResult.success_result()

    @classmethod
    async def validate_dependencies(cls, registry: Any) -> "ValidationResult":
        """Validate dependencies against ``registry``."""

        return ValidationResult.success_result()

    async def initialize(self) -> None:
        """Optional startup hook for plugins."""

        return None

    async def shutdown(self) -> None:
        """Optional shutdown hook for plugins."""

        return None

    async def execute(self, context: Any) -> Any:
        start = time.perf_counter()
        logger = getattr(self, "logging", None)
        if logger is not None:
            await logger.log(
                "info",
                "Plugin execution started",
                component="plugin",
                plugin_name=self.__class__.__name__,
                pipeline_id=getattr(context, "pipeline_id", ""),
                stage=getattr(context, "current_stage", None),
            )
        success = True
        error_type = None
        try:
            result = await self._execute_impl(context)
            return result
        except Exception as exc:
            success = False
            error_type = exc.__class__.__name__
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            metrics = getattr(self, "metrics_collector", None)
            if logger is not None:
                await logger.log(
                    "error" if not success else "info",
                    (
                        "Plugin execution failed"
                        if not success
                        else "Plugin execution succeeded"
                    ),
                    component="plugin",
                    plugin_name=self.__class__.__name__,
                    pipeline_id=getattr(context, "pipeline_id", ""),
                    stage=getattr(context, "current_stage", None),
                    error_type=error_type,
                    duration_ms=duration,
                )
            if metrics is not None:
                await metrics.record_plugin_execution(
                    pipeline_id=getattr(context, "pipeline_id", ""),
                    stage=getattr(context, "current_stage", None),
                    plugin_name=self.__class__.__name__,
                    duration_ms=duration,
                    success=success,
                    error_type=error_type,
                )


class InfrastructurePlugin(Plugin):
    """Layer 1 plugin providing infrastructure primitives."""

    infrastructure_type: str = ""
    resource_category: str = ""
    stages: List[PipelineStage] = []
    dependencies: List[str] = []


class ResourcePlugin(Plugin):
    """Layer 2 resource interface over infrastructure."""

    infrastructure_dependencies: List[str] = []
    resource_category: str = ""
    stages: List[PipelineStage] = []

    async def _track_operation(
        self,
        *,
        operation: str,
        func: Any,
        context: Any | None = None,
        **metadata: Any,
    ) -> Any:
        start = time.perf_counter()
        logger = getattr(self, "logging", None)
        if logger is not None:
            await logger.log(
                "info",
                f"{operation} started",
                component="resource",
                resource_name=getattr(self, "name", self.__class__.__name__),
                pipeline_id=(
                    getattr(context, "pipeline_id", "system") if context else "system"
                ),
            )
        success = True
        try:
            result = await func()
            return result
        except Exception as exc:
            success = False
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            metrics = getattr(self, "metrics_collector", None)
            if logger is not None:
                await logger.log(
                    "error" if not success else "info",
                    f"{operation} failed" if not success else f"{operation} succeeded",
                    component="resource",
                    resource_name=getattr(self, "name", self.__class__.__name__),
                    pipeline_id=(
                        getattr(context, "pipeline_id", "system")
                        if context
                        else "system"
                    ),
                    duration_ms=duration,
                    success=success,
                    **metadata,
                )
            if metrics is not None:
                await metrics.record_resource_operation(
                    pipeline_id=(
                        getattr(context, "pipeline_id", "system")
                        if context
                        else "system"
                    ),
                    resource_name=getattr(self, "name", self.__class__.__name__),
                    operation=operation,
                    duration_ms=duration,
                    success=success,
                    metadata=metadata,
                )


class AgentResource(ResourcePlugin):
    """Layer 3 canonical or custom agent resource."""


class ToolPlugin(Plugin):
    """Utility plugin executed via ``tool_use`` calls."""

    stages = [PipelineStage.DO]
    required_params: List[str] = []

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        raise NotImplementedError

    async def execute_function_with_retry(self, params: Dict[str, Any]) -> Any:
        for name in self.required_params:
            if name not in params:
                raise ToolExecutionError(f"Missing parameter: {name}")
        return await self.execute_function(params)


class PromptPlugin(Plugin):
    """Processing plugin typically run in ``THINK`` stage."""

    stages = [PipelineStage.THINK]


class AdapterPlugin(Plugin):
    """Input or output adapter plugin."""

    stages = [PipelineStage.INPUT, PipelineStage.OUTPUT]


class InputAdapterPlugin(AdapterPlugin):
    """Adapter executed in the ``INPUT`` stage."""

    stages = [PipelineStage.INPUT]


class OutputAdapterPlugin(AdapterPlugin):
    """Adapter executed in the ``OUTPUT`` stage."""

    stages = [PipelineStage.OUTPUT]


class FailurePlugin(Plugin):
    """Error handling plugin for the ``ERROR`` stage."""

    stages = [PipelineStage.ERROR]


@dataclass
class ValidationResult:
    success: bool
    message: str = ""

    @classmethod
    def success_result(cls) -> "ValidationResult":
        return cls(True, "")

    @classmethod
    def error_result(cls, message: str) -> "ValidationResult":
        return cls(False, message)


class ConfigurationError(Exception):
    """Raised when plugin configuration is invalid."""


@dataclass
class ReconfigResult:
    updated: bool


class AutoGeneratedPlugin(Plugin):
    """Wrapper created by :class:`PluginAutoClassifier`."""

    def __init__(
        self,
        func: Any,
        stages: list[PipelineStage],
        name: str,
        base_class: type[Plugin],
    ) -> None:
        super().__init__()
        self.func = func
        self.stages = _normalize_stages(stages)
        self.name = name
        self.base_class = base_class

    async def _execute_impl(self, context: Any) -> Any:
        return await self.func(context)
