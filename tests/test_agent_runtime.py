import pytest

from entity.core.agent import Agent, _AgentBuilder
from entity.core.plugins import Plugin
from entity.pipeline.stages import PipelineStage
from entity.workflows.base import Workflow


class ThoughtPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        last = context.conversation()[-1].content
        await context.think("msg", last)


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        msg = await context.reflect("msg")
        context.say(f"{msg}!")


@pytest.mark.asyncio
async def test_builder_runtime_executes_workflow():
    builder = _AgentBuilder()
    await builder.add_plugin(ThoughtPlugin({}))
    await builder.add_plugin(EchoPlugin({}))
    wf = Workflow(
        {PipelineStage.THINK: ["ThoughtPlugin"], PipelineStage.OUTPUT: ["EchoPlugin"]}
    )
    runtime = await builder.build_runtime(workflow=wf)
    result = await runtime.handle("hello")
    assert result == "hello!"


@pytest.mark.asyncio
async def test_agent_handle_runs_workflow():
    agent = Agent()
    await agent.add_plugin(ThoughtPlugin({}))
    await agent.add_plugin(EchoPlugin({}))
    agent.pipeline = Workflow(
        {PipelineStage.THINK: ["ThoughtPlugin"], PipelineStage.OUTPUT: ["EchoPlugin"]}
    )
    result = await agent.handle("bye")
    assert result == "bye!"
