from __future__ import annotations

"""Deprecated wrapper delegating to :class:`AgentRuntime`.

This class exists solely for backward compatibility. Prefer using
``entity.Agent`` or ``entity.core.runtime.AgentRuntime`` directly. It will be
removed in a future release.
"""

import asyncio
from typing import Any, Generic, Optional, TypeVar, cast

import warnings

from entity.core.runtime import AgentRuntime
from entity.core.state_logger import StateLogger
from entity.core.registries import SystemRegistries

ResultT = TypeVar("ResultT")


class PipelineManager(Generic[ResultT]):
    """Backwards compatible manager interface."""

    def __init__(
        self,
        capabilities: Optional[SystemRegistries] = None,
        *,
        state_logger: StateLogger | None = None,
        **kwargs: Any,
    ) -> None:
        if capabilities is None and "registries" in kwargs:
            warnings.warn(
                "'registries' is deprecated, use 'capabilities' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            capabilities = kwargs.pop("registries")
        if kwargs:
            raise TypeError(f"Unexpected arguments: {', '.join(kwargs)}")
        self._runtime = AgentRuntime(capabilities, state_logger=state_logger)
        self._capabilities = self._runtime.capabilities

    # ------------------------------------------------------------------
    @property
    def capabilities(self) -> SystemRegistries:
        return self._capabilities

    @property
    def registries(self) -> SystemRegistries:  # pragma: no cover - legacy
        """Backward compatibility alias for ``capabilities``."""

        warnings.warn(
            "'registries' is deprecated, use 'capabilities' instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._capabilities

    # ------------------------------------------------------------------
    def start_pipeline(
        self, message: str, *, max_iterations: int = 5
    ) -> asyncio.Task[ResultT]:
        task = self._runtime.start_pipeline(message, max_iterations=max_iterations)
        return cast(asyncio.Task[ResultT], task)

    async def run_pipeline(self, message: str, *, max_iterations: int = 5) -> ResultT:
        result = await self._runtime.run_pipeline(
            message, max_iterations=max_iterations
        )
        return cast(ResultT, result)

    # Delegate activity tracking --------------------------------------
    async def register(self, pipeline_id: str) -> None:  # pragma: no cover - legacy
        await self._runtime.register(pipeline_id)

    async def deregister(self, pipeline_id: str) -> None:  # pragma: no cover - legacy
        await self._runtime.deregister(pipeline_id)

    async def has_active_pipelines_async(self) -> bool:
        return await self._runtime.has_active_pipelines_async()

    def has_active_pipelines(self) -> bool:
        return self._runtime.has_active_pipelines()

    async def active_pipeline_count_async(self) -> int:
        return await self._runtime.active_pipeline_count_async()

    def active_pipeline_count(self) -> int:
        return self._runtime.active_pipeline_count()
