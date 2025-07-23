import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext


async def dummy_tool(text: str, results=None):
    if results is not None:
        results.append(text)
    return text.upper()


class ImmediatePlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        return await context.tool_use("dummy", text=context.message)


class QueuePlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        context.queue_tool_use(
            "dummy", text=context.message, results=context.get_resource("results")
        )
        return "queued"


@pytest.mark.asyncio
async def test_tool_use_immediate():
    wf = Workflow(steps={WorkflowExecutor.THINK: [ImmediatePlugin]})
    resources = {"tools": {"dummy": dummy_tool}}
    executor = WorkflowExecutor(resources, wf.steps)

    result = await executor.run("hello")
    assert result == "HELLO"


@pytest.mark.asyncio
async def test_tool_use_queued():
    results = []
    wf = Workflow(steps={WorkflowExecutor.THINK: [QueuePlugin]})
    resources = {"tools": {"dummy": dummy_tool}, "results": results}
    executor = WorkflowExecutor(resources, wf.steps)

    await executor.run("hi")
    assert results == ["hi"]
