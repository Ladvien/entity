import asyncio
import time
from datetime import datetime

from pipeline import (ConversationEntry, MetricsCollector, PipelineStage,
                      PipelineState, PluginRegistry, SystemRegistries,
                      ToolCall, ToolRegistry)
from pipeline.resources import ResourceContainer
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
        metrics=MetricsCollector(),
        current_stage=PipelineStage.DO,
    )


def test_concurrency_limit():
    state = _make_state()
    tool = SleepTool()
    tools = ToolRegistry(concurrency_limit=2)
    asyncio.run(tools.add("sleep", tool))
    registries = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    for i in range(4):
        state.pending_tool_calls.append(
            ToolCall(name="sleep", params={"delay": 0.1}, result_key=f"r{i}")
        )
    start = time.time()
    asyncio.run(execute_pending_tools(state, registries))
    duration = time.time() - start
    assert tool.calls == 4
    assert duration >= 0.2


def test_cache_ttl():
    state = _make_state()
    tool = SleepTool()
    tools = ToolRegistry(cache_ttl=5)
    asyncio.run(tools.add("sleep", tool))
    registries = SystemRegistries(ResourceContainer(), tools, PluginRegistry())
    state.pending_tool_calls.append(
        ToolCall(name="sleep", params={"delay": 0}, result_key="a")
    )
    asyncio.run(execute_pending_tools(state, registries))
    state.pending_tool_calls.append(
        ToolCall(name="sleep", params={"delay": 0}, result_key="b")
    )
    asyncio.run(execute_pending_tools(state, registries))
    assert tool.calls == 1
    assert state.stage_results["b"] == 0
    key = f"{PipelineStage.DO}:sleep"
    assert key in state.metrics.tool_durations
