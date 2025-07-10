import asyncio
from datetime import datetime

from entity.core.resources.container import ResourceContainer
from entity.core.state import (
    ConversationEntry,
    PipelineState,
    ToolCall,
)
from pipeline import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.context import PluginContext
from pipeline.tools.execution import execute_pending_tools


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
    return state


def test_execute_pending_tools_returns_mapping_by_result_key():
    state = make_state()
    capabilities = SystemRegistries(
        ResourceContainer(), ToolRegistry(), PluginRegistry()
    )
    asyncio.run(capabilities.tools.add("echo", EchoTool()))
    ctx = PluginContext(state, capabilities)
    asyncio.run(ctx.queue_tool_use("echo", result_key="echo1", text="hello"))

    results = asyncio.run(execute_pending_tools(state, capabilities))

    assert results == {"echo1": "hello"}
    ctx = PluginContext(state, capabilities)
    assert ctx.load("echo1") == "hello"
