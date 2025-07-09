from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from entity.core.plugins.base import ToolExecutionError
from entity.core.state import ToolCall
from pipeline.state import PipelineState, MetricsCollector
from entity.core.registries import SystemRegistries


async def execute_pending_tools(
    state: PipelineState, registries: SystemRegistries
) -> Dict[str, Any]:
    """Run queued tools respecting registry options."""
    results: Dict[str, Any] = {}
    if not state.pending_tool_calls:
        return results
    tools = registries.tools
    sem = asyncio.Semaphore(tools.concurrency_limit)

    async def run_call(call: ToolCall) -> None:
        cached = await tools.get_cached_result(call.name, call.params)
        if cached is not None:
            result = cached
            duration = 0.0
        else:
            tool = tools.get(call.name)
            if tool is None:
                raise ToolExecutionError(f"Tool '{call.name}' not found")
            start = time.perf_counter()
            async with sem:
                result = await tool.execute_function(call.params)
            duration = time.perf_counter() - start
            await tools.cache_result(call.name, call.params, result)
        results[call.result_key] = result
        state.stage_results[call.result_key] = result
        if state.metrics:
            key = f"{state.current_stage}:{call.name}"
            state.metrics.record_tool_duration(key, duration)

    await asyncio.gather(*(run_call(c) for c in list(state.pending_tool_calls)))
    return results
