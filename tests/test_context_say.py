import pytest

from entity.workflow.workflow import Workflow

from entity.plugins.context import WorkflowContext, PluginContext
from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


def test_say_rejects_invalid_stage() -> None:
    ctx = WorkflowContext()
    ctx.current_stage = WorkflowExecutor.THINK
    with pytest.raises(RuntimeError):
        ctx.say("nope")


@pytest.mark.asyncio
async def test_plugin_say_invalid_stage() -> None:
    class BadPlugin(Plugin):
        stage = WorkflowExecutor.THINK

        async def _execute_impl(self, context: PluginContext) -> str:
            context.say("oops")
            return "ignored"

    wf_dict = {WorkflowExecutor.THINK: [BadPlugin]}
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"memory": memory}
    wf = Workflow.from_dict(wf_dict, resources)
    executor = WorkflowExecutor(resources, wf)

    with pytest.raises(RuntimeError):
        await executor.execute("hi")
