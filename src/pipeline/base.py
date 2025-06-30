from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .context import PluginContext
from .stages import PipelineStage


class BasePlugin(ABC):
    """Base class for all pipeline plugins."""

    stages: List[PipelineStage] = []

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.logger = None

    async def execute(self, context: PluginContext) -> Any:
        if self.logger:
            self.logger.info(
                "Plugin execution started",
                plugin=self.__class__.__name__,
                pipeline_id=context.pipeline_id,
                stage=str(context.current_stage),
            )
        start = time.time()
        try:
            result = await self._execute_impl(context)
            context.record_plugin_duration(self.__class__.__name__, time.time() - start)
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Plugin execution failed",
                    plugin=self.__class__.__name__,
                    pipeline_id=context.pipeline_id,
                    stage=str(context.current_stage),
                    error=str(e),
                    exc_info=True,
                )
            raise

    @abstractmethod
    async def _execute_impl(self, context: PluginContext) -> Any:
        pass
