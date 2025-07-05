from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, TypeVar, cast

from interfaces import ToolPluginProtocol

from registry import SystemRegistries

from ..state import PipelineState, ToolCall
from .base import RetryOptions


ResultT = TypeVar("ResultT")


async def execute_tool(
    tool: ToolPluginProtocol[ResultT],
    call: ToolCall,
    state: PipelineState,
    options: RetryOptions,
) -> ResultT:
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
                async_func = cast(Callable[[Dict[str, Any]], Awaitable[ResultT]], func)
                return await async_func(call.params)
            sync_func = cast(Callable[[Dict[str, Any]], ResultT], func)
            return sync_func(call.params)
        except Exception:
            if attempt == options.max_retries:
                raise
            await asyncio.sleep(options.delay)
    raise RuntimeError("Tool execution failed")


async def execute_pending_tools(
    state: PipelineState, registries: SystemRegistries
) -> Dict[str, ResultT]:
    """Execute queued tools and return their results by ``result_key``."""

    results: Dict[str, ResultT] = {}
    cache = registries.resources.get("cache")
    for call in list(state.pending_tool_calls):
        tool = registries.tools.get(call.name)
        if not tool:
            error_msg = f"Error: tool {call.name} not found"
            state.stage_results[call.result_key] = error_msg
            results[call.result_key] = cast(ResultT, error_msg)
            continue
        tool = cast(ToolPluginProtocol[ResultT], tool)

        options = RetryOptions(
            max_retries=getattr(tool, "max_retries", 1),
            delay=getattr(tool, "retry_delay", 1.0),
        )
        cache_key = None
        if cache:
            import hashlib
            import json

            params_repr = json.dumps(call.params, sort_keys=True)
            cache_key = (
                "tool:"
                + hashlib.sha256(f"{call.name}:{params_repr}".encode()).hexdigest()
            )
            cached = await cache.get(cache_key)
            if cached is not None:
                state.stage_results[call.result_key] = cached
                results[call.result_key] = cast(ResultT, cached)
                state.pending_tool_calls.remove(call)
                continue
        try:
            result = await execute_tool(tool, call, state, options)
            state.stage_results[call.result_key] = result
            results[call.result_key] = result
            if cache and cache_key:
                await cache.set(cache_key, result)
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
            results[call.result_key] = cast(ResultT, err)
            state.metrics.record_tool_error(
                call.name,
                cast(str, state.current_stage and str(state.current_stage)),
                state.pipeline_id,
                str(exc),
            )
        finally:
            state.pending_tool_calls.remove(call)
    return results


__all__ = ["execute_tool", "execute_pending_tools"]
