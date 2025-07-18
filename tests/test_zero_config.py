import pytest
from entity.core.agent import Agent
from entity.core.plugins import Plugin
from entity.pipeline.stages import PipelineStage
from entity.pipeline.workflow import Pipeline, Workflow


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        user = next((e.content for e in context.conversation() if e.role == "user"), "")
        context.say(f"reply: {user}")


@pytest.mark.asyncio
async def test_zero_config_defaults() -> None:
    agent = Agent()
    await agent.add_plugin(EchoPlugin({}))
    wf = Workflow({PipelineStage.OUTPUT: ["EchoPlugin"]})
    agent.pipeline = Pipeline(builder=agent.builder, workflow=wf)
    runtime = await agent.build_runtime()
    result = await runtime.handle("hi")
    assert result == "reply: hi"
