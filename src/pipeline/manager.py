from __future__ import annotations

"""Deprecated wrapper delegating to :class:`AgentRuntime`.

This class exists solely for backward compatibility. Prefer using
``entity.Agent`` or ``entity.core.runtime.AgentRuntime`` directly. It will be
removed in a future release.
"""

import asyncio
import warnings
from typing import Any, Generic, TypeVar, cast

from entity.core.registries import SystemRegistries
from entity.core.runtime import AgentRuntime
from entity.core.state_logger import StateLogger

ResultT = TypeVar("ResultT")


class PipelineManager(Generic[ResultT]):
    """Backwards compatible manager interface."""

    def __init__(
        self,
        capabilities: SystemRegistries,
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
        if "state_file" in kwargs or "snapshots_dir" in kwargs:
            warnings.warn(
                "'state_file' and 'snapshots_dir' are removed; use StateLogger",
                DeprecationWarning,
                stacklevel=2,
            )
            kwargs.pop("state_file", None)
            kwargs.pop("snapshots_dir", None)
        if kwargs:
            raise TypeError(f"Unexpected arguments: {', '.join(kwargs)}")
        self._runtime = AgentRuntime(capabilities, state_logger=state_logger)
        self._capabilities = self._runtime.capabilities

    # ------------------------------------------------------------------
    @property
    def capabilities(self) -> SystemRegistries:
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
        return bool(await self._runtime.has_active_pipelines_async())

    def has_active_pipelines(self) -> bool:
        return bool(self._runtime.has_active_pipelines())

    async def active_pipeline_count_async(self) -> int:
        return int(await self._runtime.active_pipeline_count_async())

    def active_pipeline_count(self) -> int:
        return int(self._runtime.active_pipeline_count())
