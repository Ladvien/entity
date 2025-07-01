from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .context import PluginContext
from .exceptions import CircuitBreakerTripped, PluginExecutionError
from .stages import PipelineStage


class BasePlugin(ABC):
    """Base class for all pipeline plugins.

    Implements **Explicit Stage Assignment (17)** and
    **Observable by Design (16)** by requiring subclasses to
    declare their stages and by logging each execution.
    """

    stages: List[PipelineStage] = []

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self.logger = None
        self.failure_threshold = int(self._config.get("failure_threshold", 3))
        self.failure_reset_timeout = float(
            self._config.get("failure_reset_timeout", 60.0)
        )
        self._failure_count = 0
        self._last_failure = 0.0

    @property
    def config(self) -> Dict[str, Any]:
        """Return the plugin configuration."""
        return self._config

    async def execute(self, context: PluginContext) -> Any:
        if self.logger:
            self.logger.info(
                "Plugin execution started",
                plugin=self.__class__.__name__,
                pipeline_id=context.pipeline_id,
                stage=str(context.current_stage),
            )
        start = time.time()
        if (
            self._failure_count >= self.failure_threshold
            and time.time() - self._last_failure < self.failure_reset_timeout
        ):
            raise CircuitBreakerTripped(self.__class__.__name__)
        if time.time() - self._last_failure >= self.failure_reset_timeout:
            self._failure_count = 0
        try:
            result = await self._execute_impl(context)
            context.record_plugin_duration(self.__class__.__name__, time.time() - start)
            self._failure_count = 0
            return result
        except Exception as exc:  # noqa: BLE001 - converted to PluginExecutionError
            if self.logger:
                self.logger.error(
                    "Plugin execution failed",
                    plugin=self.__class__.__name__,
                    pipeline_id=context.pipeline_id,
                    stage=str(context.current_stage),
                    error=str(exc),
                    exc_info=True,
                )
            self._failure_count += 1
            self._last_failure = time.time()
            raise PluginExecutionError(self.__class__.__name__, exc) from exc

    @abstractmethod
    async def _execute_impl(self, context: PluginContext) -> Any:
        pass
