from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict

from .context import PluginContext, SystemRegistries
from .registries import PluginRegistry, ResourceRegistry, ToolRegistry
from .stages import PipelineStage
from .state import (
    ConversationEntry,
    FailureInfo,
    MetricsCollector,
    PipelineState,
    ToolCall,
)


async def execute_pipeline(request: Any, registries: SystemRegistries) -> Any:
    state = PipelineState(
        conversation=[
            ConversationEntry(content=str(request), role="user", timestamp=datetime.now())
        ],
        response=None,
        prompt="",
        stage_results={},
        pending_tool_calls=[],
        metadata={},
        pipeline_id=str(uuid.uuid4()),
        current_stage=None,
        metrics=MetricsCollector(),
    )

    for stage in [PipelineStage.PARSE, PipelineStage.THINK, PipelineStage.DO, PipelineStage.REVIEW, PipelineStage.DELIVER]:
        await execute_stage(stage, state, registries)
        if state.response is not None:
            break

    if state.response is None:
        state.response = create_default_response("No response generated", state.pipeline_id)
    return state.response


async def execute_stage(stage: PipelineStage, state: PipelineState, registries: SystemRegistries) -> None:
    state.current_stage = stage
    context = PluginContext(state, registries)
    plugins = registries.plugins.get_for_stage(stage)
    for plugin in plugins:
        try:
            await plugin.execute(context)
            if state.pending_tool_calls:
                results = await execute_pending_tools(state, registries)
                for call, result in results.items():
                    context.add_conversation_entry(
                        content=f"Tool result: {result}",
                        role="system",
                        metadata={"tool_name": call.name, "stage": str(stage)},
                    )
                state.pending_tool_calls.clear()
        except Exception as e:
            failure = FailureInfo(
                stage=str(stage),
                plugin_name=plugin.__class__.__name__,
                error_type="plugin_error",
                error_message=str(e),
                original_exception=e,
                context_snapshot={"pipeline_id": state.pipeline_id},
                timestamp=datetime.now(),
            )
            context.add_failure(failure)
            if stage != PipelineStage.ERROR:
                await execute_stage(PipelineStage.ERROR, state, registries)
                return


def create_default_response(message: str, pipeline_id: str) -> Dict[str, Any]:
    return {
        "message": message,
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "type": "default_response",
    }


async def execute_pending_tools(state: PipelineState, registries: SystemRegistries) -> Dict[ToolCall, Any]:
    results = {}
    for call in list(state.pending_tool_calls):
        tool = registries.tools.get(call.name)
        if not tool:
            results[call] = f"Unknown tool: {call.name}"
            continue
        try:
            if hasattr(tool, "execute_function_with_retry"):
                result = await tool.execute_function_with_retry(call.params)
            else:
                result = await tool.execute_function(call.params)
            results[call] = result
            state.metrics.record_tool_execution(
                tool_name=call.name,
                stage=str(state.current_stage),
                pipeline_id=state.pipeline_id,
                result_key=call.result_key,
                source=call.source,
            )
        except Exception as e:
            results[call] = f"Error: {e}"
            state.metrics.record_tool_error(
                tool_name=call.name,
                stage=str(state.current_stage),
                pipeline_id=state.pipeline_id,
                error=str(e),
            )
    return results
