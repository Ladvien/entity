import asyncio
import pytest

from pipeline import PipelineStage
from pipeline.base_plugins import BasePlugin
from entity import AgentBuilder


class ReplyPlugin(BasePlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        context.set_response("ok")


@pytest.mark.integration
def test_legacy_config_without_workflow_executes():
    builder = AgentBuilder()
    builder.add_plugin(ReplyPlugin({}))
    runtime = builder.build_runtime()
    result = asyncio.run(runtime.run_pipeline("hi"))
    assert result == "ok"
