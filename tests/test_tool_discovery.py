import asyncio
from datetime import datetime

from pipeline import (
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
    PipelineStage,
)
from entity.core.context import PluginContext
from entity.core.state import ConversationEntry, PipelineState


class DummyTool:
    async def execute_function(self, params):
        return params.get("value")


async def _make_context():
    tools = ToolRegistry()
    await tools.add("alpha_tool", DummyTool())
    await tools.add("beta_tool", DummyTool())
    caps = SystemRegistries(
        resources=PluginRegistry(), tools=tools, plugins=PluginRegistry()
    )
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
        current_stage=PipelineStage.DO,
    )
    return PluginContext(state, caps)


def test_discover_all_tools():
    ctx = asyncio.run(_make_context())
    tools = ctx.discover_tools()
    names = {name for name, _ in tools}
    assert names == {"alpha_tool", "beta_tool"}


def test_discover_tools_by_name():
    ctx = asyncio.run(_make_context())
    tools = ctx.discover_tools(name="beta")
    assert len(tools) == 1
    assert tools[0][0] == "beta_tool"
