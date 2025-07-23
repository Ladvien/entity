import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext


class LogPlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        await context.logger.log(
            "info",
            "running",
            stage=context.current_stage,
            plugin_name=self.__class__.__name__,
        )
        await context.metrics_collector.record_plugin_execution(
            plugin_name=self.__class__.__name__,
            stage=context.current_stage,
            duration_ms=0.0,
            success=True,
        )
        return context.message or ""


class OutputPlugin(Plugin):
    stage = WorkflowExecutor.OUTPUT

    async def _execute_impl(self, context: PluginContext) -> str:
        await context.logger.log(
            "info",
            "output",
            stage=context.current_stage,
            plugin_name=self.__class__.__name__,
        )
        await context.metrics_collector.record_plugin_execution(
            plugin_name=self.__class__.__name__,
            stage=context.current_stage,
            duration_ms=0.0,
            success=True,
        )
        context.say("done")
        return "done"


@pytest.mark.asyncio
async def test_logging_and_metrics_per_stage():
    wf = Workflow(
        steps={
            WorkflowExecutor.THINK: [LogPlugin],
            WorkflowExecutor.OUTPUT: [OutputPlugin],
        }
    )
    executor = WorkflowExecutor({}, wf.steps)
    result = await executor.run("hi")

    assert result == "done"

    logs = executor.resources["logging"].records
    metrics = executor.resources["metrics_collector"].records

    assert [r["stage"] for r in logs] == [
        WorkflowExecutor.THINK,
        WorkflowExecutor.OUTPUT,
    ]
    assert [m["stage"] for m in metrics] == [
        WorkflowExecutor.THINK,
        WorkflowExecutor.OUTPUT,
    ]
