import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext

pytest.skip("Tool execution tests require external resources", allow_module_level=True)
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.tools.web_search import web_search


class ImmediatePlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        return await context.tool_use("search", query=context.message)


class QueuePlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        context.queue_tool_use(
            "search", query=context.message, results=context.get_resource("results")
        )
        return "queued"


@pytest.mark.asyncio
async def test_tool_use_immediate():
    wf = Workflow(steps={WorkflowExecutor.THINK: [ImmediatePlugin]})
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"tools": {"search": web_search}, "memory": memory}
    executor = WorkflowExecutor(resources, wf.steps)

    result = await executor.run("OpenAI")
    assert "OpenAI" in result


@pytest.mark.asyncio
async def test_tool_use_queued():
    results = []
    wf = Workflow(steps={WorkflowExecutor.THINK: [QueuePlugin]})
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"tools": {"search": web_search}, "results": results, "memory": memory}
    executor = WorkflowExecutor(resources, wf.steps)

    await executor.run("Python programming")
    assert any("Python" in r for r in results)
