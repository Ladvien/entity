import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
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
    resources = {"tools": {"search": web_search}}
    executor = WorkflowExecutor(resources, wf.steps)

    result = await executor.run("OpenAI")
    assert "OpenAI" in result


@pytest.mark.asyncio
async def test_tool_use_queued():
    results = []
    wf = Workflow(steps={WorkflowExecutor.THINK: [QueuePlugin]})
    resources = {"tools": {"search": web_search}, "results": results}
    executor = WorkflowExecutor(resources, wf.steps)

    await executor.run("Python programming")
    assert any("Python" in r for r in results)
