import pytest

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from entity.plugins.context import PluginContext


@pytest.mark.asyncio
async def test_output_plugin_sets_response_on_second_iteration():
    calls: list[int] = []

    class TwoPassOutputPlugin(Plugin):
        stage = WorkflowExecutor.OUTPUT

        async def _execute_impl(self, context: PluginContext) -> str:
            calls.append(context.loop_count)
            if context.loop_count >= 1:
                context.say("final")
            return "ignored"

    wf = {WorkflowExecutor.OUTPUT: [TwoPassOutputPlugin]}
    executor = WorkflowExecutor({}, wf)

    result = await executor.run("hello")

    assert result == "final"
    assert calls == [0, 1]
