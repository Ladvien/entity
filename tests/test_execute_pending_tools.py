import asyncio
from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginRegistry,
    ResourceRegistry,
    SystemRegistries,
    ToolCall,
    ToolRegistry,
)
from pipeline.pipeline import execute_pending_tools


class EchoTool:
    async def execute_function(self, params):  # pragma: no cover - simple stub
        return params["text"]


def make_state():
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    state.pending_tool_calls.append(
        ToolCall(name="echo", params={"text": "hello"}, result_key="echo1")
    )
    return state


def test_execute_pending_tools_returns_mapping_by_result_key():
    state = make_state()
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), PluginRegistry())
    asyncio.run(registries.tools.add("echo", EchoTool()))

    results = asyncio.run(execute_pending_tools(state, registries))

    assert results == {"echo1": "hello"}
    assert state.stage_results["echo1"] == "hello"
