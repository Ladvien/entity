"""Pipeline execution utilities.

This module delegates tool execution to
``pipeline.tools.execution`` to keep logic centralized.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any, Dict

from registry import SystemRegistries

from .context import ConversationEntry, PluginContext
from .errors import create_static_error_response
from .exceptions import (CircuitBreakerTripped, PipelineError,
                         PluginExecutionError, ResourceError,
                         ToolExecutionError)
from .logging import get_logger, reset_request_id, set_request_id
from .manager import PipelineManager
from .metrics import MetricsCollector
from .observability.metrics import get_metrics_server
from .observability.tracing import start_span
from .serialization import dumps_state, loads_state
from .stages import PipelineStage
from .state import FailureInfo, PipelineState
from .tools.execution import execute_pending_tools

logger = get_logger(__name__)


def generate_pipeline_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def create_default_response(message: str, pipeline_id: str) -> Dict[str, Any]:
    return {
        "message": message,
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "type": "default_response",
    }


async def execute_stage(
    stage: PipelineStage, state: PipelineState, registries: SystemRegistries
) -> None:
    state.current_stage = stage
    stage_plugins = registries.plugins.get_plugins_for_stage(stage)
    start = time.perf_counter()
    async with start_span(f"stage.{stage.name.lower()}"):
        for plugin in stage_plugins:
            context = PluginContext(state, registries)
            token = set_request_id(state.pipeline_id)
            try:
                await plugin.execute(context)
                if state.pending_tool_calls:
                    tool_results = await execute_pending_tools(state, registries)
                    for call in state.pending_tool_calls:
                        result = tool_results.get(call.result_key)
                        context.add_conversation_entry(
                            content=f"Tool result: {result}",
                            role="system",
                            metadata={"tool_name": call.name, "stage": str(stage)},
                        )
                    state.pending_tool_calls.clear()
            except CircuitBreakerTripped as exc:
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type="circuit_breaker",
                    error_message=str(exc),
                    original_exception=exc,
                )
                return
            except PluginExecutionError as exc:
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.original_exception.__class__.__name__,
                    error_message=str(exc.original_exception),
                    original_exception=exc.original_exception,
                )
                return
            except ToolExecutionError as exc:
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=exc.tool_name,
                    error_type=exc.original_exception.__class__.__name__,
                    error_message=str(exc.original_exception),
                    original_exception=exc.original_exception,
                )
                return
            except ResourceError as exc:
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    original_exception=exc,
                )
                return
            except PipelineError as exc:
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    original_exception=exc,
                )
                return
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Unexpected plugin exception",
                    exc_info=exc,
                    extra={
                        "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                        "stage": str(stage),
                    },
                )

                message = exc.args[0] if exc.args else str(exc)
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.__class__.__name__,
                    error_message=message,
                    original_exception=exc,
                )
                if isinstance(exc, KeyError):
                    raise
            finally:
                reset_request_id(token)
    duration = time.perf_counter() - start
    state.metrics.record_stage_duration(str(stage), duration)


async def execute_pipeline(
    user_message: str,
    registries: SystemRegistries,
    *,
    state_file: str | None = None,
    snapshots_dir: str | None = None,
    pipeline_manager: PipelineManager | None = None,
    return_metrics: bool = False,
    state: PipelineState | None = None,
) -> Dict[str, Any] | tuple[Dict[str, Any], MetricsCollector]:
    if state is None:
        if state_file and os.path.exists(state_file):
            if state_file.endswith((".mpk", ".msgpack")):
                with open(state_file, "rb") as fh:
                    state = loads_state(fh.read())
            else:
                with open(state_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                state = PipelineState.from_dict(data)
            state.failure_info = None
        else:
            state = PipelineState(
                conversation=[
                    ConversationEntry(
                        content=user_message, role="user", timestamp=datetime.now()
                    )
                ],
                pipeline_id=generate_pipeline_id(),
                metrics=MetricsCollector(),
            )
    start = time.time()
    if pipeline_manager is not None:
        await pipeline_manager.register(state.pipeline_id)
    try:
        async with registries.resources:
            async with start_span("pipeline.execute"):
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
                        await execute_stage(stage, state, registries)
                    finally:
                        if state_file:
                            if state_file.endswith((".mpk", ".msgpack")):
                                with open(state_file, "wb") as fh:
                                    fh.write(dumps_state(state))
                            else:
                                with open(state_file, "w", encoding="utf-8") as fh:
                                    json.dump(state.to_dict(), fh)
                        if snapshots_dir:
                            os.makedirs(snapshots_dir, exist_ok=True)
                            snap_path = os.path.join(
                                snapshots_dir,
                                f"{state.pipeline_id}_{stage.name.lower()}.json",
                            )
                            with open(snap_path, "w", encoding="utf-8") as fh:
                                json.dump(state.to_dict(), fh)
                    if state.failure_info:
                        break
                    state.last_completed_stage = stage

        if state.failure_info:
            try:
                await execute_stage(PipelineStage.ERROR, state, registries)
            except Exception:
                result = create_static_error_response(state.pipeline_id)
                return (result, state.metrics) if return_metrics else result
            if state.response is None:
                result = create_static_error_response(state.pipeline_id)
                return (result, state.metrics) if return_metrics else result
            result = state.response
        elif state.response is None:
            result = create_default_response("No response generated", state.pipeline_id)
        else:
            result = state.response
        return (result, state.metrics) if return_metrics else result
    finally:
        if pipeline_manager is not None:
            await pipeline_manager.deregister(state.pipeline_id)
        state.metrics.record_pipeline_duration(time.time() - start)
        if state_file and os.path.exists(state_file) and state.failure_info is None:
            os.remove(state_file)
        server = get_metrics_server()
        if server is not None:
            server.update(state.metrics)


__all__ = [
    "generate_pipeline_id",
    "create_default_response",
    "execute_stage",
    "execute_pipeline",
]
