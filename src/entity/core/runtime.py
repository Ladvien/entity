from __future__ import annotations

"""Agent runtime executing pipeline stages sequentially."""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set

from pipeline.pipeline import (
    create_default_response,
    create_static_error_response,
    execute_stage,
    generate_pipeline_id,
)
from pipeline.observability.metrics import MetricsServerManager
from pipeline.observability.tracing import start_span
from pipeline.logging import get_logger
from pipeline.metrics import MetricsCollector
from pipeline.state import ConversationEntry, FailureInfo, PipelineState
from pipeline.stages import PipelineStage
from registry import SystemRegistries

from .state_logger import StateLogger


logger = get_logger(__name__)


@dataclass
class AgentRuntime:
    """Execute messages through configured pipeline stages."""

    registries: SystemRegistries | None = None
    state_logger: StateLogger | None = None

    def __post_init__(self) -> None:
        self._tasks: Set[asyncio.Task[Dict[str, Any]]] = set()
        self._active: Set[str] = set()
        self._lock = asyncio.Lock()
        if self.registries is None:
            raise ValueError("AgentRuntime requires system registries")

    # ------------------------------------------------------------------
    # Concurrency helpers
    # ------------------------------------------------------------------
    def start_pipeline(
        self, message: str, *, max_iterations: int = 5
    ) -> asyncio.Task[Dict[str, Any]]:
        """Begin processing ``message`` in a background task."""

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        task = loop.create_task(
            self.run_pipeline(message, max_iterations=max_iterations)
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def register(self, pipeline_id: str) -> None:
        async with self._lock:
            self._active.add(pipeline_id)

    async def deregister(self, pipeline_id: str) -> None:
        async with self._lock:
            self._active.discard(pipeline_id)

    async def has_active_pipelines_async(self) -> bool:
        async with self._lock:
            self._tasks = {t for t in self._tasks if not t.done()}
            return bool(self._tasks or self._active)

    def has_active_pipelines(self) -> bool:
        self._tasks = {t for t in self._tasks if not t.done()}
        return bool(self._tasks or self._active)

    async def active_pipeline_count_async(self) -> int:
        async with self._lock:
            self._tasks = {t for t in self._tasks if not t.done()}
            return max(len(self._tasks), len(self._active))

    def active_pipeline_count(self) -> int:
        self._tasks = {t for t in self._tasks if not t.done()}
        return max(len(self._tasks), len(self._active))

    # ------------------------------------------------------------------
    async def run_pipeline(
        self, message: str, max_iterations: int = 5
    ) -> Dict[str, Any]:
        """Execute the pipeline for ``message``."""

        if self.registries is None:
            raise ValueError("AgentRuntime requires system registries")

        state = PipelineState(
            conversation=[
                ConversationEntry(
                    content=message, role="user", timestamp=datetime.now()
                )
            ],
            pipeline_id=generate_pipeline_id(),
            metrics=MetricsCollector(),
        )

        start = time.time()
        await self.register(state.pipeline_id)
        try:
            async with self.registries.resources:
                async with start_span("pipeline.execute"):
                    while True:
                        state.iteration += 1
                        for stage in [
                            PipelineStage.PARSE,
                            PipelineStage.THINK,
                            PipelineStage.DO,
                            PipelineStage.REVIEW,
                            PipelineStage.DELIVER,
                        ]:
                            if (
                                state.last_completed_stage is not None
                                and stage.value <= state.last_completed_stage.value
                            ):
                                continue
                            try:
                                await execute_stage(stage, state, self.registries)
                            finally:
                                if self.state_logger is not None:
                                    self.state_logger.log(state, stage)
                                logger.info(
                                    "stage complete",
                                    extra={
                                        "stage": str(stage),
                                        "pipeline_id": state.pipeline_id,
                                        "iteration": state.iteration,
                                    },
                                )
                            if state.failure_info:
                                break
                            state.last_completed_stage = stage

                        if (
                            state.response is not None
                            and state.last_completed_stage == PipelineStage.DELIVER
                        ):
                            break

                        if (
                            state.failure_info is not None
                            or state.iteration >= max_iterations
                        ):
                            if (
                                state.response is None
                                and state.failure_info is None
                                and state.iteration >= max_iterations
                            ):
                                state.failure_info = FailureInfo(
                                    stage="iteration_guard",
                                    plugin_name="pipeline",
                                    error_type="max_iterations",
                                    error_message=f"Reached {max_iterations} iterations",
                                    original_exception=RuntimeError(
                                        "max iteration limit reached"
                                    ),
                                )
                            break

                        state.last_completed_stage = None

                if state.failure_info:
                    try:
                        await execute_stage(PipelineStage.ERROR, state, self.registries)
                        if self.state_logger is not None:
                            self.state_logger.log(state, PipelineStage.ERROR)
                        await execute_stage(
                            PipelineStage.DELIVER, state, self.registries
                        )
                    except Exception:
                        return create_static_error_response(state.pipeline_id).to_dict()
                    if state.response is None:
                        return create_static_error_response(state.pipeline_id).to_dict()
                    return state.response

                if state.response is None:
                    return create_default_response(
                        "No response generated", state.pipeline_id
                    )
                return state.response
        finally:
            await self.deregister(state.pipeline_id)
            if state.metrics:
                state.metrics.record_pipeline_duration(time.time() - start)
            server = MetricsServerManager.get()
            if server is not None and state.metrics:
                server.update(state.metrics)

    async def handle(self, message: str) -> Dict[str, Any]:
        """Alias for :meth:`run_pipeline`."""

        return await self.run_pipeline(message)

    async def __aenter__(self) -> "AgentRuntime":
        if self.registries is None:
            raise ValueError("AgentRuntime requires system registries")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Any,
    ) -> None:
        if hasattr(self.registries.resources, "shutdown_all"):
            await self.registries.resources.shutdown_all()
