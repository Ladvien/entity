import pytest

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
from entity.workflow.executor import WorkflowExecutor


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
