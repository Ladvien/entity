import asyncio
import time
from datetime import datetime

from entity.core.resources.container import ResourceContainer
from entity.core.state import (
    ConversationEntry,
    PipelineState,
    ToolCall,
)
from pipeline import PluginRegistry, SystemRegistries, ToolRegistry, PipelineStage
from entity.core.context import PluginContext
from pipeline.tools.execution import execute_pending_tools


class SleepTool:
    def __init__(self) -> None:
        self.calls = 0

    async def execute_function(self, params):
        self.calls += 1
        await asyncio.sleep(params.get("delay", 0))
        return params.get("delay", 0)


def _make_state() -> PipelineState:
    return PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now()),
        ],
        pipeline_id="1",
        current_stage=PipelineStage.DO,
    )


def test_concurrency_limit():
    state = _make_state()
    tool = SleepTool()
    tools = ToolRegistry(concurrency_limit=2)
    asyncio.run(tools.add("sleep", tool))
    capabilities = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    ctx = PluginContext(state, capabilities)
    for i in range(4):
        asyncio.run(ctx.queue_tool_use("sleep", result_key=f"r{i}", delay=0.1))
    start = time.time()
    asyncio.run(execute_pending_tools(state, capabilities))
    duration = time.time() - start
    assert tool.calls == 4
    assert duration >= 0.2


def test_cache_ttl():
    state = _make_state()
    tool = SleepTool()
    tools = ToolRegistry(cache_ttl=5)
    asyncio.run(tools.add("sleep", tool))
    capabilities = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    ctx = PluginContext(state, capabilities)
    asyncio.run(ctx.queue_tool_use("sleep", result_key="a", delay=0))
    asyncio.run(execute_pending_tools(state, capabilities))
    asyncio.run(ctx.queue_tool_use("sleep", result_key="b", delay=0))
    asyncio.run(execute_pending_tools(state, capabilities))
    assert tool.calls == 1
    ctx = PluginContext(state, capabilities)
    assert ctx.recall("b") == 0
    key = f"{PipelineStage.DO}:sleep"
    assert key in state.metrics.tool_durations
