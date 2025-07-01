from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from registry import SystemRegistries

from .context import PluginContext
from .manager import PipelineManager
from .stages import PipelineStage
from .state import (ConversationEntry, FailureInfo, MetricsCollector,
                    PipelineState)
from .tools.execution import execute_pending_tools


def generate_pipeline_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def create_default_response(message: str, pipeline_id: str) -> Dict[str, Any]:
    return {
        "message": message,
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "type": "default_response",
    }


STATIC_ERROR_RESPONSE = {
    "error": "System error occurred",
    "message": "An unexpected error prevented processing your request.",
    "error_id": None,
    "timestamp": None,
    "type": "static_fallback",
}


def create_static_error_response(pipeline_id: str) -> Dict[str, Any]:
    response = STATIC_ERROR_RESPONSE.copy()
    response["error_id"] = pipeline_id
    response["timestamp"] = datetime.now().isoformat()
    return response


async def execute_stage(
    stage: PipelineStage, state: PipelineState, registries: SystemRegistries
) -> None:
    state.current_stage = stage
    stage_plugins = registries.plugins.get_for_stage(stage)
    for plugin in stage_plugins:
        context = PluginContext(state, registries)
        try:
            await plugin.execute(context)
        except Exception as exc:
            state.failure_info = FailureInfo(
                stage=str(stage),
                plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                error_type="plugin_error",
                error_message=str(exc),
                original_exception=exc,
            )
            return
        if state.pending_tool_calls:
            tool_results = await execute_pending_tools(state, registries)
            for call in list(state.pending_tool_calls):
                result = tool_results.get(call.result_key)
                context.add_conversation_entry(
                    content=f"Tool result: {result}",
                    role="system",
                    metadata={"tool_name": call.name, "stage": str(stage)},
                )
            state.pending_tool_calls.clear()


async def execute_pipeline(
    user_message: str,
    registries: SystemRegistries,
    pipeline_manager: PipelineManager | None = None,
    return_metrics: bool = False,
) -> Dict[str, Any] | tuple[Dict[str, Any], MetricsCollector]:
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
        for stage in [
            PipelineStage.PARSE,
            PipelineStage.THINK,
            PipelineStage.DO,
            PipelineStage.REVIEW,
            PipelineStage.DELIVER,
        ]:
            await execute_stage(stage, state, registries)
            if state.failure_info:
                break

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
