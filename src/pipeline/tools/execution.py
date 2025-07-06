import asyncio
import hashlib
import json
import time
from typing import Any, Awaitable, Callable, Dict, TypeVar, cast

from common_interfaces import ToolPluginProtocol
from registry import SystemRegistries

from ..exceptions import ToolExecutionError
from ..state import FailureInfo, PipelineState, ToolCall
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
                raise ToolExecutionError(
                    call.name,
                    RuntimeError("Tool lacks execution method"),
                    call.result_key,
                )
            if asyncio.iscoroutinefunction(func):
                async_func = cast(Callable[[Dict[str, Any]], Awaitable[ResultT]], func)
                return await async_func(call.params)
            sync_func = cast(Callable[[Dict[str, Any]], ResultT], func)
            return sync_func(call.params)
        except Exception:
            if attempt == options.max_retries:
                raise
            await asyncio.sleep(options.delay)
    raise ToolExecutionError(
        call.name, RuntimeError("Tool execution failed"), call.result_key
    )


async def execute_pending_tools(
    state: PipelineState, registries: SystemRegistries
) -> Dict[str, ResultT]:
    """Execute queued tools and return their results by ``result_key``."""

    results: Dict[str, ResultT] = {}
    cache = registries.resources.get("cache")
    calls = list(state.pending_tool_calls)
    concurrency = getattr(registries.tools, "concurrency_limit", None)
    semaphore = asyncio.Semaphore(concurrency) if concurrency else None

    async def run_call(call: ToolCall) -> None:
        tool = registries.tools.get(call.name)
        if not tool:
            raise ToolExecutionError(call.name)
        tool = cast(ToolPluginProtocol[ResultT], tool)

        options = RetryOptions(
            max_retries=getattr(tool, "max_retries", 1),
            delay=getattr(tool, "retry_delay", 1.0),
        )

        async def _execute() -> None:
            cache_key: str | None = None
            cached = await registries.tools.get_cached_result(call.name, call.params)
            if cached is None and cache:
                params_repr = json.dumps(call.params, sort_keys=True)
                cache_key = (
                    "tool:"
                    + hashlib.sha256(f"{call.name}:{params_repr}".encode()).hexdigest()
                )
                cached = await cache.get(cache_key)
            if cached is not None:
                state.stage_results[call.result_key] = cached
                if (
                    state.max_stage_results is not None
                    and len(state.stage_results) > state.max_stage_results
                ):
                    oldest = next(iter(state.stage_results))
                    if oldest != call.result_key:
                        state.stage_results.pop(oldest, None)
                results[call.result_key] = cast(ResultT, cached)
                state.metrics.record_tool_execution(
                    call.name,
                    cast(str, state.current_stage and str(state.current_stage)),
                    state.pipeline_id,
                    call.result_key,
                    call.source,
                )
                return

            start = time.time()
            try:
                result = await execute_tool(tool, call, state, options)
            except Exception as exc:
                err = f"Error: {exc}"
                state.stage_results[call.result_key] = err
                if (
                    state.max_stage_results is not None
                    and len(state.stage_results) > state.max_stage_results
                ):
                    oldest = next(iter(state.stage_results))
                    if oldest != call.result_key:
                        state.stage_results.pop(oldest, None)
                results[call.result_key] = cast(ResultT, err)
                state.metrics.record_tool_error(
                    call.name,
                    cast(str, state.current_stage and str(state.current_stage)),
                    state.pipeline_id,
                    str(exc),
                )
                state.failure_info = FailureInfo(
                    stage=str(state.current_stage),
                    plugin_name=call.name,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    original_exception=exc,
                )
                raise ToolExecutionError(call.name, exc, call.result_key) from exc
            else:
                state.stage_results[call.result_key] = result
                if (
                    state.max_stage_results is not None
                    and len(state.stage_results) > state.max_stage_results
                ):
                    oldest = next(iter(state.stage_results))
                    if oldest != call.result_key:
                        state.stage_results.pop(oldest, None)
                results[call.result_key] = result
                if cache and cache_key:
                    await cache.set(cache_key, result)
                await registries.tools.cache_result(call.name, call.params, result)
                duration = time.time() - start
                state.metrics.record_tool_execution(
                    call.name,
                    cast(str, state.current_stage and str(state.current_stage)),
                    state.pipeline_id,
                    call.result_key,
                    call.source,
                )
                state.metrics.record_tool_duration(
                    call.name,
                    cast(str, state.current_stage and str(state.current_stage)),
                    duration,
                )

        if semaphore:
            async with semaphore:
                await _execute()
        else:
            await _execute()
        state.pending_tool_calls.remove(call)

    tasks = [asyncio.create_task(run_call(c)) for c in calls]
    if tasks:
        await asyncio.gather(*tasks)
    return results


__all__ = ["execute_tool", "execute_pending_tools"]
