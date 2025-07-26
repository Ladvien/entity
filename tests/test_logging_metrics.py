import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.plugins.base import Plugin

pytest.skip(
    "Metrics integration not available in this environment",
    allow_module_level=True,
)
from entity.plugins.context import PluginContext
from entity.resources.logging import LogCategory
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


class LogPlugin(Plugin):
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context: PluginContext) -> str:
        return context.message or ""


class OutputPlugin(Plugin):
    stage = WorkflowExecutor.OUTPUT

    async def _execute_impl(self, context: PluginContext) -> str:
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
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    executor = WorkflowExecutor({"memory": memory}, wf.steps)
    result = await executor.execute("hi")

    assert result == "done"

    logs = executor.resources["logging"].records
    metrics = executor.resources["metrics_collector"].records

    assert [r["fields"]["category"] for r in logs[:2]] == [
        LogCategory.PLUGIN_LIFECYCLE.value,
        LogCategory.PLUGIN_LIFECYCLE.value,
    ]
    assert [r["fields"]["stage"] for r in logs[:2]] == [
        WorkflowExecutor.THINK,
        WorkflowExecutor.THINK,
    ]
    assert [r["fields"]["stage"] for r in logs[2:]] == [
        WorkflowExecutor.OUTPUT,
        WorkflowExecutor.OUTPUT,
    ]
    assert [m["stage"] for m in metrics] == [
        WorkflowExecutor.THINK,
        WorkflowExecutor.OUTPUT,
    ]
