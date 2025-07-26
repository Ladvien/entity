import pytest

from entity.plugins.context import PluginContext
from entity.plugins.smart_selector import SmartToolSelectorPlugin

pytest.skip("Tool selection tests require external resources", allow_module_level=True)
from entity.tools.registry import clear_registry, register_tool
from entity.workflow import Workflow, WorkflowExecutor
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


async def tool_a():
    return "A"


async def tool_b():
    return "B"


@pytest.mark.asyncio
async def test_discover_tools_filtered():
    clear_registry()
    register_tool(tool_a, name="a", category="letters")
    register_tool(tool_b, name="b", category="symbols")
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx = PluginContext({"memory": memory}, user_id="t")
    tools = ctx.discover_tools(category="letters")
    assert [t.name for t in tools] == ["a"]


@pytest.mark.asyncio
async def test_smart_selector_picks_correct_tool():
    clear_registry()
    register_tool(tool_a, name="a")
    register_tool(tool_b, name="b")
    wf = Workflow(steps={WorkflowExecutor.THINK: [SmartToolSelectorPlugin]})
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"tools": {"a": tool_a, "b": tool_b}, "memory": memory}
    executor = WorkflowExecutor(resources, wf.steps)

    result_a = await executor.run("run a")
    assert result_a == "A"

    result_b = await executor.run("use b")
    assert result_b == "B"
