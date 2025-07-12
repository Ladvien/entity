import asyncio
import pytest

from pipeline import PipelineStage, execute_pipeline
from entity.core.plugins import Plugin
from entity.core.builder import _AgentBuilder


class ReplyPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        context.set_response("ok")


@pytest.mark.integration
def test_legacy_config_without_workflow_executes():
    builder = _AgentBuilder()
    builder.add_plugin(ReplyPlugin({}))
    runtime = builder.build_runtime()
    result = asyncio.run(execute_pipeline("hi", runtime.capabilities))
    assert result == "ok"
