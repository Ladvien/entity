import pytest

from entity.plugins.context import PluginContext
from entity.plugins.smart_selector import SmartToolSelectorPlugin
from entity.tools.registry import clear_registry, register_tool
from entity.workflow import Workflow, WorkflowExecutor


async def tool_a():
    return "A"


async def tool_b():
    return "B"


@pytest.mark.asyncio
async def test_discover_tools_filtered():
    clear_registry()
    register_tool(tool_a, name="a", category="letters")
    register_tool(tool_b, name="b", category="symbols")
    ctx = PluginContext({}, user_id="t")
    tools = ctx.discover_tools(category="letters")
    assert [t.name for t in tools] == ["a"]


@pytest.mark.asyncio
async def test_smart_selector_picks_correct_tool():
    clear_registry()
    register_tool(tool_a, name="a")
    register_tool(tool_b, name="b")
    wf = Workflow(steps={WorkflowExecutor.THINK: [SmartToolSelectorPlugin]})
    resources = {"tools": {"a": tool_a, "b": tool_b}}
    executor = WorkflowExecutor(resources, wf.steps)

    result_a = await executor.run("run a")
    assert result_a == "A"

    result_b = await executor.run("use b")
    assert result_b == "B"
