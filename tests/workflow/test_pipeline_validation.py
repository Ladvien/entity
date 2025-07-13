import pytest

from entity.core.plugins import Plugin
from entity.core.agent import Agent
from entity.pipeline.stages import PipelineStage
from entity.pipeline.workflow import Pipeline


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        context.say("ok")


@pytest.mark.asyncio
async def test_pipeline_raises_on_unknown_plugin():
    builder = Agent().builder
    await builder.add_plugin(EchoPlugin({}))

    mapping = {PipelineStage.OUTPUT: ["EchoPlugin", "MissingPlugin"]}
    with pytest.raises(
        KeyError,
        match="Plugin 'MissingPlugin' referenced in stage 'output' is not registered",
    ):
        Pipeline(builder=builder, workflow=mapping)
