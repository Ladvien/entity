from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .registry import ClassRegistry

import yaml

from .context import LLMResponse, PluginContext, SimpleContext
from .stages import PipelineStage

logger = logging.getLogger(__name__)

Self = TypeVar("Self", bound="BasePlugin")


@dataclass
class ValidationResult:
    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(True)

    @classmethod
    def error(cls, message: str) -> "ValidationResult":
        return cls(False, error_message=message)


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

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, context: PluginContext | SimpleContext):
        logger.info(
            "Plugin execution started",
            extra={
                "plugin": self.__class__.__name__,
                "stage": str(context.current_stage),
                "pipeline_id": context.pipeline_id,
            },
        )
        start = time.time()
        try:
            result = await self._execute_impl(context)
            duration = time.time() - start
            context._state.metrics.record_plugin_duration(
                self.__class__.__name__, str(context.current_stage), duration
            )
            logger.info(
                "Plugin execution finished",
                extra={
                    "plugin": self.__class__.__name__,
                    "stage": str(context.current_stage),
                    "duration": duration,
                },
            )
            return result
        except Exception as e:
            logger.exception(
                "Plugin execution failed",
                extra={
                    "plugin": self.__class__.__name__,
                    "stage": str(context.current_stage),
                    "error": str(e),
                },
            )
            raise

    @abstractmethod
    async def _execute_impl(self, context: PluginContext | SimpleContext):
        pass

    async def call_llm(
        self, context: PluginContext, prompt: str, purpose: str
    ) -> "LLMResponse":
        llm = context.get_resource("ollama")
        if llm is None:
            raise RuntimeError("LLM resource 'ollama' not available")

        context._state.metrics.record_llm_call(
            self.__class__.__name__, str(context.current_stage), purpose
        )

        if hasattr(llm, "generate"):
            response = await llm.generate(prompt)
        else:
            func = getattr(llm, "__call__", None)
            if asyncio.iscoroutinefunction(func):
                response = await func(prompt)
            else:
                response = func(prompt)

        return LLMResponse(content=str(response))

    # --- Validation & Reconfiguration ---
    @classmethod
    def validate_config(cls: Type[Self], config: Dict) -> ValidationResult:
        return ValidationResult.success()

    @classmethod
    def validate_dependencies(
        cls: Type[Self], registry: "ClassRegistry"
    ) -> ValidationResult:
        return ValidationResult.success()

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
        except Exception as e:
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
        for attempt in range(max_retries + 1):
        max_retry_count = self.max_retries if max_retries is None else max_retries
        retry_delay_seconds = self.retry_delay if delay is None else delay
        for attempt in range(max_retry_count + 1):
            try:
                return await self.execute_function(params)
            except Exception:
                if attempt == max_retry_count:
                    raise
                await asyncio.sleep(retry_delay_seconds)

    def validate_tool_params(self, params: Dict[str, Any]) -> bool:
        return True

    async def execute_with_timeout(
        self, context: PluginContext | SimpleContext, timeout: int = 30
    ):
        return await asyncio.wait_for(self.execute(context), timeout=timeout)

    async def _execute_impl(self, context: PluginContext | SimpleContext):
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

    async def _execute_impl(self, context: PluginContext | SimpleContext):
        if inspect.iscoroutinefunction(self.func):
            result = await self.func(context)
        else:
            result = self.func(context)
        if isinstance(result, str) and not context.has_response():
            context.set_response(result)


class PluginAutoClassifier:
    """Utility to generate plugin classes from simple functions."""

    @staticmethod
    def classify(
        plugin_func: Any, user_hints: Optional[Dict[str, Any]] | None = None
    ) -> AutoGeneratedPlugin:
        """Classify ``plugin_func`` and return an :class:`AutoGeneratedPlugin`."""

        hints = user_hints or {}
        try:
            source = inspect.getsource(plugin_func)
        except OSError:
            source = ""

        if any(k in source for k in ["think", "reason", "analyze"]):
            stage = PipelineStage.THINK
            base = PromptPlugin
        elif any(k in source for k in ["parse", "validate", "check"]):
            stage = PipelineStage.PARSE
            base = AdapterPlugin
        elif any(k in source for k in ["return", "response", "answer"]):
            stage = PipelineStage.DO
            base = (
                ToolPlugin
                if any(x in source for x in ["use_tool", "execute_tool", "tool"])
                else PromptPlugin
            )
        else:
            stage = PipelineStage.DO
            base = ToolPlugin

        if "stage" in hints:
            stage = PipelineStage.from_str(str(hints["stage"]))

        priority = int(hints.get("priority", 50))
        name = hints.get("name", plugin_func.__name__)

        return AutoGeneratedPlugin(
            func=plugin_func,
            stages=[stage],
            priority=priority,
            name=name,
            base_class=base,
        )
