import asyncio

import pytest
from entity import Agent


class ParsePlugin(BasePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        context.cache("parsed", True)


class ThinkPlugin(BasePlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        context.cache("thought", True)


class RespondPlugin(BasePlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        context.set_response("ok")


@pytest.mark.integration
def test_full_agent_pipeline():
    agent = Agent()
    agent.add_plugin(ParsePlugin())
    agent.add_plugin(ThinkPlugin())
    agent.add_plugin(RespondPlugin())

    agent._runtime = agent.builder.build_runtime()
    result = asyncio.run(agent.handle("hi"))
    assert result == "ok"
