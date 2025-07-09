from __future__ import annotations

"""Pipeline component: base plugins."""

import asyncio
import inspect
import json
import logging
import time
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar

import yaml
from pydantic import ValidationError

from common_interfaces.base_plugin import BasePlugin as BasePluginInterface
from plugins.builtin.config_models import PLUGIN_CONFIG_MODELS, DefaultConfigModel

from ..exceptions import CircuitBreakerTripped, PipelineError, PluginExecutionError
from ..logging import get_logger
from ..observability.utils import execute_with_observability
from ..reliability import RetryPolicy
from ..stages import PipelineStage
from ..validation import ValidationResult

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from ..context import PluginContext
    from ..initializer import ClassRegistry
    from ..state import LLMResponse

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


class BasePlugin(BasePluginInterface):
    stages: List[PipelineStage]
    dependencies: List[str] = []
    max_retries: int = 1
    retry_delay: float = 0.0

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls.__module__ in {__name__, "pipeline.base_plugins.base"}:
            return

        mro_names = {base.__name__ for base in cls.__mro__}

        has_explicit = "stages" in cls.__dict__
        if "ToolPlugin" in mro_names and not has_explicit:
            cls.stages = [PipelineStage.DO]
        elif "PromptPlugin" in mro_names and not has_explicit:
            cls.stages = [PipelineStage.THINK]
        elif "AdapterPlugin" in mro_names and not has_explicit:
            cls.stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

        stages = getattr(cls, "stages", None)
        if stages is None:
            return
        if not stages:
            raise ValueError(f"{cls.__name__} must define a non-empty 'stages' list")

        skip_validation = getattr(cls, "skip_stage_validation", False)
        normalized: List[PipelineStage | Any] = []
        for stage in stages:
            if isinstance(stage, PipelineStage):
                normalized.append(stage)
                continue
            if isinstance(stage, str):
                try:
                    normalized.append(PipelineStage.from_str(stage))
                except ValueError:
                    if skip_validation:
                        normalized.append(stage)
                        continue
                    raise ValueError(
                        f"Invalid stage '{stage}' for {cls.__name__}"
                    ) from None
                continue
            if skip_validation:
                normalized.append(stage)
                continue
            raise ValueError(
                f"All items in {cls.__name__}.stages must be PipelineStage instances"
            )

        cls.stages = normalized
        cls._explicit_stages = has_explicit

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self.failure_threshold = int(self.config.get("failure_threshold", 3))
        self.failure_reset_timeout = float(
            self.config.get("failure_reset_timeout", 60.0)
        )
        self.max_retries = int(self.config.get("max_retries", self.max_retries))
        self.retry_delay = float(self.config.get("retry_delay", self.retry_delay))
        self._failure_count = 0
        self._last_failure = 0.0
        self.config_version = 1
        self._config_history: List[Dict] = [self.config.copy()]

    async def execute(self, context: "PluginContext") -> Any:
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
            policy = RetryPolicy(
                attempts=self.max_retries + 1, backoff=self.retry_delay
            )
            return await policy.execute(self._execute_impl, context)

        policy = RetryPolicy(
            attempts=self.max_retries + 1,
            backoff=self.retry_delay,
        )

        async def run_with_retry() -> Any:
            return await policy.execute(run)

        try:
            result = await execute_with_observability(
                run_with_retry,
                logger=self.logger,
                metrics=context.metrics,
                plugin=self.__class__.__name__,
                stage=str(context.current_stage),
                pipeline_id=context.pipeline_id,
            )
            self._failure_count = 0
            return result
        except PipelineError:
            self._failure_count += 1
            self._last_failure = time.time()
            raise
        except Exception as exc:  # noqa: BLE001 - convert to PluginExecutionError
            self._failure_count += 1
            self._last_failure = time.time()
            raise PluginExecutionError(self.__class__.__name__, exc) from exc

    @abstractmethod
    async def _execute_impl(self, context: "PluginContext"):
        pass

    async def call_llm(
        self,
        context: "PluginContext",
        prompt: str,
        purpose: str,
        functions: list[dict[str, Any]] | None = None,
    ) -> "LLMResponse":
        from ..context import LLMResponse

        llm = context.get_llm()
        if llm is None:
            raise RuntimeError("LLM resource not available")

        cache = context.get_resource("cache")
        cache_key = None
        cached = None
        if cache:
            import hashlib

            cache_key = "llm:" + hashlib.sha256(prompt.encode()).hexdigest()
            if hasattr(cache, "get_semantic"):
                cached = await cache.get_semantic(prompt)
            if cached is None:
                cached = await cache.get(cache_key)
            if cached is not None:
                return LLMResponse(content=str(cached))

        context.record_llm_call(self.__class__.__name__, purpose)

        start = time.time()

        if hasattr(llm, "generate"):
            sig = inspect.signature(llm.generate)
            if "functions" in sig.parameters:
                response = await llm.generate(prompt, functions)
            else:
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

        if isinstance(response, LLMResponse):
            llm_response = response
        else:
            llm_response = LLMResponse(content=str(response))

        if cache and cache_key is not None:
            await cache.set(cache_key, llm_response.content)
            if hasattr(cache, "set_semantic"):
                await cache.set_semantic(prompt, llm_response.content)

        tokens = (llm_response.prompt_tokens or 0) + (
            llm_response.completion_tokens or 0
        )
        if tokens:
            context.metrics.record_llm_tokens(
                self.__class__.__name__, str(context.current_stage), tokens
            )
        if llm_response.cost:
            context.metrics.record_llm_cost(
                self.__class__.__name__, str(context.current_stage), llm_response.cost
            )

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
        model_cls = PLUGIN_CONFIG_MODELS.get(cls.__name__, DefaultConfigModel)
        try:
            model_cls(**config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    @classmethod
    def validate_dependencies(
        cls: Type[Self], registry: "ClassRegistry"
    ) -> ValidationResult:
        return ValidationResult.success_result()

    def supports_runtime_reconfiguration(self) -> bool:
        return True

    async def validate_runtime(self) -> "ValidationResult":
        """Verify the plugin can operate in the current runtime environment."""

        return ValidationResult.success_result()

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
            self._config_history.append(new_config.copy())
            self.config_version += 1
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

    async def rollback_config(self, version: int | None = None) -> ReconfigResult:
        """Revert to a previous configuration version."""

        if version is None:
            version = self.config_version - 1
        if version < 1 or version >= self.config_version:
            return ReconfigResult(False, error_message="Invalid version")
        target = self._config_history[version - 1]
        old = self.config
        try:
            self.config = target.copy()
            await self._handle_reconfiguration(old, self.config)
            self.config_version = version
            self._config_history = self._config_history[:version]
            return ReconfigResult(True)
        except Exception as exc:  # noqa: BLE001
            self.config = old
            return ReconfigResult(False, error_message=str(exc))

    async def _handle_reconfiguration(self, old_config: Dict, new_config: Dict):
        """Override this method to handle configuration changes.

        Called after validation passes and ``self.config`` has been updated.
        """
        pass  # Default: no special handling needed

    # --- Convenience constructors ---
    @classmethod
    def from_dict(cls: Type[Self], config: Dict) -> Self:
        """Create plugin from ``config`` with CONFIG VALIDATION ONLY."""

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
