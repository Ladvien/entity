import types
import pytest

from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry
from entity.pipeline.stages import PipelineStage
from entity.pipeline.pipeline import execute_pipeline


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        msg = context.conversation()[-1].content
        context.say(msg)


@pytest.mark.asyncio
async def test_pipeline_without_validators_runs():
    caps = types.SimpleNamespace(
        resources={},
        tools=types.SimpleNamespace(),
        plugins=PluginRegistry(),
    )
    await caps.plugins.register_plugin_for_stage(EchoPlugin({}), PipelineStage.OUTPUT)
    result = await execute_pipeline("hi", caps)
    assert result == "hi"
