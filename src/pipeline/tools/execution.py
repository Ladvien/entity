from __future__ import annotations

import asyncio
from typing import Any, Dict, cast

from ..registries import SystemRegistries
from ..state import PipelineState, ToolCall
from .base import RetryOptions


async def _execute_tool(
    tool: Any, call: ToolCall, state: PipelineState, options: RetryOptions
) -> Any:
    for attempt in range(options.max_retries + 1):
        try:
            if hasattr(tool, "execute_function_with_retry"):
                return await tool.execute_function_with_retry(
                    call.params, options.max_retries, options.delay
                )
            if hasattr(tool, "execute_function"):
                return await tool.execute_function(call.params)
            func = getattr(tool, "run", None)
            if func is None:
                raise RuntimeError("Tool lacks execution method")
            if asyncio.iscoroutinefunction(func):
                return await func(call.params)
            return func(call.params)
        except Exception:
            if attempt == options.max_retries:
                raise
            await asyncio.sleep(options.delay)


async def execute_pending_tools(
    state: PipelineState, registries: SystemRegistries
) -> Dict[str, Any]:
    """Execute queued tools and return their results by ``result_key``."""

    results: Dict[str, Any] = {}
    for call in list(state.pending_tool_calls):
        tool = registries.tools.get(call.name)
        if not tool:
            error_msg = f"Error: tool {call.name} not found"
            state.stage_results[call.result_key] = error_msg
            results[call.result_key] = error_msg
            continue

        options = RetryOptions(
            max_retries=getattr(tool, "max_retries", 1),
            delay=getattr(tool, "retry_delay", 1.0),
        )
        try:
            result = await _execute_tool(tool, call, state, options)
            state.stage_results[call.result_key] = result
            results[call.result_key] = result
            state.metrics.record_tool_execution(
                call.name,
                cast(str, state.current_stage and str(state.current_stage)),
                state.pipeline_id,
                call.result_key,
                call.source,
            )
        except Exception as exc:
            err = f"Error: {exc}"
            state.stage_results[call.result_key] = err
            results[call.result_key] = err
            state.metrics.record_tool_error(
                call.name,
                cast(str, state.current_stage and str(state.current_stage)),
                state.pipeline_id,
                str(exc),
            )
        finally:
            state.pending_tool_calls.remove(call)
    return results
