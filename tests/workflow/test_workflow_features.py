import pytest

from entity.core.agent import Agent
from entity.core.plugins import Plugin
from entity.pipeline.stages import PipelineStage
from entity.pipeline.workflow import Pipeline
from entity.workflows.base import Workflow


class MarkerPlugin(Plugin):
    stages = [PipelineStage.THINK]
    executed = False

    async def _execute_impl(self, context):
        MarkerPlugin.executed = True


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        context.say("ok")


class BaseWF(Workflow):
    stage_map = {PipelineStage.THINK: ["MarkerPlugin"]}


class ChildWF(BaseWF):
    stage_map = {PipelineStage.OUTPUT: ["EchoPlugin"]}


@pytest.mark.asyncio
async def test_conditional_stage_skip():
    builder = Agent().builder
    await builder.add_plugin(MarkerPlugin({}))
    await builder.add_plugin(EchoPlugin({}))

    wf = ChildWF(conditions={PipelineStage.THINK: lambda _state: False})
    pipeline = Pipeline(builder=builder, workflow=wf)
    runtime = await pipeline.build_runtime()
    result = await runtime.handle("hi")
    assert result == "ok"
    assert not MarkerPlugin.executed


def test_workflow_inheritance():
    wf = ChildWF()
    assert PipelineStage.THINK in wf.stages
    assert PipelineStage.OUTPUT in wf.stages
