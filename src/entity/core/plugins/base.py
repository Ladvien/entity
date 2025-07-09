from __future__ import annotations

"""Base plugin classes used by the Entity framework.

These classes mirror the minimal architecture described in
``architecture/general.md`` and avoid importing ``pipeline.base_plugins``.
They offer a small, easy to understand surface for plugin authors.
"""

from typing import Any, Dict, List

import asyncio
import time

from pipeline.logging import get_logger
from pipeline.stages import PipelineStage
from pipeline.errors import ToolExecutionError


class BasePlugin:
    """Foundation for all plugins."""

    stages: List[PipelineStage]
    dependencies: List[str] = []
    failure_threshold: int = 3
    failure_reset_timeout: float = 60.0
    max_retries: int = 1
    retry_delay: float = 0.0

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    async def execute(self, context: Any) -> Any:
        for attempt in range(self.max_retries + 1):
            try:
                return await self._execute_impl(context)
            except Exception:  # noqa: BLE001 - propagate after retries
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay)
        return None

    async def _execute_impl(self, context: Any) -> Any:
        """Execute plugin logic in the pipeline."""
        raise NotImplementedError

    async def call_llm(self, context: Any, prompt: str, purpose: str = "") -> Any:
        start = time.perf_counter()
        response = await context.call_llm(context, prompt, purpose=purpose)
        duration = time.perf_counter() - start
        self.logger.info(
            "LLM call completed",
            extra={
                "plugin": self.__class__.__name__,
                "stage": str(getattr(context, "current_stage", "")),
                "purpose": purpose,
                "prompt_length": len(prompt),
                "response_length": len(getattr(response, "content", "")),
                "pipeline_id": getattr(context, "pipeline_id", ""),
                "duration": duration,
            },
        )
        return response


class ResourcePlugin(BasePlugin):
    """Infrastructure plugin providing persistent resources."""


class ToolPlugin(BasePlugin):
    """Utility plugin executed via ``tool_use`` calls."""

    required_params: List[str] = []

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        raise NotImplementedError

    async def execute_function_with_retry(self, params: Dict[str, Any]) -> Any:
        for name in self.required_params:
            if name not in params:
                raise ToolExecutionError(f"Missing parameter: {name}")
        for attempt in range(self.max_retries + 1):
            try:
                return await self.execute_function(params)
            except Exception as exc:
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay)
        raise RuntimeError("unreachable")


class PromptPlugin(BasePlugin):
    """Processing plugin typically run in ``THINK`` stage."""

    stages = [PipelineStage.THINK]


class AdapterPlugin(BasePlugin):
    """Input or output adapter plugin."""

    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]


class FailurePlugin(BasePlugin):
    """Error handling plugin for the ``ERROR`` stage."""

    stages = [PipelineStage.ERROR]
