from __future__ import annotations

import asyncio
from typing import Any, Dict

from entity.core.plugins import ToolExecutionError
from entity.core.state import ToolCall
from ..state import PipelineState
from entity.core.context import PluginContext
from entity.core.registries import SystemRegistries


async def execute_pending_tools(
    state: PipelineState, registries: SystemRegistries, *, user_id: str
) -> Dict[str, Any]:
    """Run queued tools respecting registry options."""
    results: Dict[str, Any] = {}
    if not state.pending_tool_calls:
        return results
    tools = registries.tools
    sem = asyncio.Semaphore(tools.concurrency_limit)
    context = PluginContext(state, registries, user_id=user_id)

    async def run_call(call: ToolCall) -> None:
        tool = tools.get(call.name)
        if tool is None:
            raise ToolExecutionError(f"Tool '{call.name}' not found")
        async with sem:
            result = await tool.execute_function(call.params)
        results[call.result_key] = result
        await context.think(call.result_key, result)

    await asyncio.gather(*(run_call(c) for c in list(state.pending_tool_calls)))
    return results
