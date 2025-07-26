import pytest

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from entity.plugins.context import PluginContext
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


@pytest.mark.asyncio
async def test_output_plugin_sets_response_on_second_iteration():
    calls: list[int] = []

    class TwoPassOutputPlugin(Plugin):
        supported_stages = [WorkflowExecutor.OUTPUT]

        async def _execute_impl(self, context: PluginContext) -> str:
            calls.append(context.loop_count)
            if context.loop_count >= 1:
                context.say("final")
            return "ignored"

    from entity.workflow.workflow import Workflow

    wf_dict = {WorkflowExecutor.OUTPUT: [TwoPassOutputPlugin]}
    wf = Workflow.from_dict(wf_dict, {})
    executor = WorkflowExecutor({}, wf)

    result = await executor.execute("hello")

    assert result == "final"
    assert calls == [0, 1]
