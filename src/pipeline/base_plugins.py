from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar

import yaml

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .context import PluginContext, SimpleContext
    from .state import LLMResponse

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .initializer import ClassRegistry

from .exceptions import CircuitBreakerTripped, PluginExecutionError
from .logging import get_logger
from .observability.utils import execute_with_observability
from .stages import PipelineStage
from .validation import ValidationResult

logger = logging.getLogger(__name__)

Self = TypeVar("Self", bound="BasePlugin")


@dataclass
class ReconfigResult:
    success: bool
    error_message: Optional[str] = None
    requires_restart: bool = False
    warnings: List[str] = field(default_factory=list)


class ConfigurationError(Exception):
    pass


class BasePlugin(ABC):
    stages: List[PipelineStage]
    priority: int = 50
    dependencies: List[str] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls.__module__ in {__name__, "pipeline.plugins.base"}:
            return

        if "ToolPlugin" in [base.__name__ for base in cls.__mro__]:
            return

        stages = getattr(cls, "stages", None)
        if not stages:
            raise ValueError(f"{cls.__name__} must define a non-empty 'stages' list")

        if any(not isinstance(stage, PipelineStage) for stage in stages):
            raise ValueError(
                f"All items in {cls.__name__}.stages must be PipelineStage instances"
            )

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self.failure_threshold = int(self.config.get("failure_threshold", 3))
        self.failure_reset_timeout = float(
            self.config.get("failure_reset_timeout", 60.0)
        )
        self._failure_count = 0
        self._last_failure = 0.0

    async def execute(self, context: PluginContext | SimpleContext) -> Any:
        """Execute plugin with logging, metrics and circuit breaker."""

        def circuit_open() -> bool:
            if self._failure_count < self.failure_threshold:
                return False
            if time.time() - self._last_failure > self.failure_reset_timeout:
                self._failure_count = 0
                return False
            return True

        if circuit_open():
            raise CircuitBreakerTripped(self.__class__.__name__)

        async def run() -> Any:
            return await self._execute_impl(context)

<<<<<<< HEAD
        return await execute_with_observability(
            run,
            logger=self.logger,
            metrics=context.metrics,
            plugin=self.__class__.__name__,
            stage=str(context.current_stage),
        )
=======
        try:
            result = await execute_with_observability(
                run,
                logger=self.logger,
                metrics=context._get_state().metrics,
                plugin=self.__class__.__name__,
                stage=str(context.current_stage),
            )
            self._failure_count = 0
            return result
        except Exception as exc:  # noqa: BLE001 - convert to PluginExecutionError
            self._failure_count += 1
            self._last_failure = time.time()
            raise PluginExecutionError(self.__class__.__name__, exc) from exc
>>>>>>> 687b80743a969fc60f52facd6803c0968786989e

    @abstractmethod
    async def _execute_impl(self, context: "PluginContext"):
        pass

    async def call_llm(
        self, context: "PluginContext", prompt: str, purpose: str
    ) -> "LLMResponse":
        from .context import LLMResponse

        llm = context.get_llm()
        if llm is None:
            raise RuntimeError("LLM resource not available")

        context.record_llm_call(self.__class__.__name__, purpose)

        start = time.time()

        if hasattr(llm, "generate"):
            response = await llm.generate(prompt)
        else:
            func = getattr(llm, "__call__", None)
            if func is None:
                raise RuntimeError("LLM resource is not callable")
            if asyncio.iscoroutinefunction(func):
                response = await func(prompt)
            else:
                response = func(prompt)

        duration = time.time() - start
        context.record_llm_duration(self.__class__.__name__, duration)

        llm_response = LLMResponse(content=str(response))
        self.logger.info(
            "LLM call completed",
            extra={
                "plugin": self.__class__.__name__,
                "stage": str(context.current_stage),
                "purpose": purpose,
                "prompt_length": len(prompt),
                "response_length": len(llm_response.content),
                "duration": duration,
                "pipeline_id": context.pipeline_id,
            },
        )

        return llm_response

    # --- Validation & Reconfiguration ---
    @classmethod
    def validate_config(cls: Type[Self], config: Dict) -> ValidationResult:
        return ValidationResult.success_result()

    @classmethod
    def validate_dependencies(
        cls: Type[Self], registry: "ClassRegistry"
    ) -> ValidationResult:
        return ValidationResult.success_result()

    def supports_runtime_reconfiguration(self) -> bool:
        return True

    async def reconfigure(self, new_config: Dict) -> ReconfigResult:
        validation_result = self.validate_config(new_config)
        if not validation_result.success:
            return ReconfigResult(
                success=False,
                error_message=f"Configuration validation failed: {validation_result.error_message}",
            )

        if not self.supports_runtime_reconfiguration():
            return ReconfigResult(
                success=False,
                requires_restart=True,
                error_message="This plugin requires application restart for configuration changes",
            )

        old_config = self.config
        try:
            self.config = new_config
            await self._handle_reconfiguration(old_config, new_config)
            return ReconfigResult(success=True)
        except Exception as e:  # noqa: BLE001
            self.config = old_config
            return ReconfigResult(
                success=False, error_message=f"Reconfiguration failed: {e}"
            )

    async def on_dependency_reconfigured(
        self, dependency_name: str, old_config: Dict, new_config: Dict
    ) -> bool:
        return True

    async def _handle_reconfiguration(self, old_config: Dict, new_config: Dict):
        """Override this method to handle configuration changes.

        Called after validation passes and ``self.config`` has been updated.
        """
        pass  # Default: no special handling needed

    # --- Convenience constructors ---
    @classmethod
    def from_dict(cls: Type[Self], config: Dict) -> Self:
        """Create plugin from ``config`` with CONFIG VALIDATION ONLY.

        .. warning::
            This does **not** validate dependencies.  Use only for testing,
            development or when dependencies are known to exist.  Production
            systems should rely on four-phase initialization.
        """
        result = cls.validate_config(config)
        if not result.success:
            raise ConfigurationError(
                f"{cls.__name__} config validation failed: {result.error_message}"
            )
        return cls(config)

    @classmethod
    def from_yaml(cls: Type[Self], yaml_content: str) -> Self:
        """Parse YAML then delegate to :meth:`from_dict` (config validation only)."""
        config = yaml.safe_load(yaml_content)
        return cls.from_dict(config)

    @classmethod
    def from_json(cls: Type[Self], json_content: str) -> Self:
        """Parse JSON then delegate to :meth:`from_dict` (config validation only)."""
        config = json.loads(json_content)
        return cls.from_dict(config)


class ResourcePlugin(BasePlugin):
    async def initialize(self) -> None:
        """Optional async initialization hook."""
        return None

    async def health_check(self) -> bool:
        """Return ``True`` if the resource is healthy."""
        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Return metrics about this resource."""
        return {"status": "healthy"}


class ToolPlugin(BasePlugin):
    """Base class for tool plugins executed outside the pipeline."""

    required_params: List[str] = []

    def _validate_required_params(self, params: Dict[str, Any]) -> bool:
        """Ensure all :attr:`required_params` are present in ``params``."""
        missing = [p for p in self.required_params if params.get(p) is None]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        return True

    def validate_tool_params(self, params: Dict[str, Any]) -> bool:
        """Public hook for validating tool parameters."""
        return self._validate_required_params(params)

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.max_retries = int(self.config.get("max_retries", 1))
        self.retry_delay = float(self.config.get("retry_delay", 1.0))

    async def execute_function(self, params: Dict[str, Any]):
        raise NotImplementedError()

    async def execute_function_with_retry(
        self,
        params: Dict[str, Any],
        max_retries: int | None = None,
        delay: float | None = None,
    ):
        self.validate_tool_params(params)
        max_retry_count = self.max_retries if max_retries is None else max_retries
        retry_delay_seconds = self.retry_delay if delay is None else delay
        for attempt in range(max_retry_count + 1):
            try:
                return await self.execute_function(params)
            except Exception:  # noqa: BLE001
                if attempt == max_retry_count:
                    raise
                await asyncio.sleep(retry_delay_seconds)

    async def execute_with_timeout(self, context: "PluginContext", timeout: int = 30):
        return await asyncio.wait_for(self.execute(context), timeout=timeout)

    async def _execute_impl(self, context: "PluginContext"):
        """Tools are not executed in the pipeline directly."""
        pass


class PromptPlugin(BasePlugin):
    pass


class AdapterPlugin(BasePlugin):
    pass


class FailurePlugin(BasePlugin):
    pass


class AutoGeneratedPlugin(BasePlugin):
    def __init__(
        self,
        func,
        stages: List[PipelineStage],
        priority: int,
        name: str,
        base_class: Optional[type] = None,
    ):
        super().__init__()
        self.func = func
        self.stages = stages
        self.priority = priority
        self.name = name
        if base_class and base_class is not BasePlugin:
            self.__class__.__bases__ = (base_class,)

    async def _execute_impl(self, context: "PluginContext") -> None:
        if not inspect.iscoroutinefunction(self.func):
            raise TypeError(
                f"Plugin function '{getattr(self.func, '__name__', 'unknown')}' must be async"
            )
        result = await self.func(context)
        if isinstance(result, str) and not context.has_response():
            context.set_response(result)


__all__ = [
    "BasePlugin",
    "ResourcePlugin",
    "ToolPlugin",
    "PromptPlugin",
    "AdapterPlugin",
    "FailurePlugin",
    "AutoGeneratedPlugin",
    "PluginAutoClassifier",
    "ConfigurationError",
    "ReconfigResult",
    "ValidationResult",
]

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .plugins.classifier import PluginAutoClassifier
else:  # pragma: no cover - runtime import for compatibility
    from .plugins.classifier import PluginAutoClassifier  # type: ignore  # noqa: E402
