import asyncio

import pytest

from entity import Agent
from pipeline import PipelineStage


class ParsePlugin:
    stages = [PipelineStage.PARSE]

    async def execute(self, context):
        context.set_stage_result("parsed", True)


class ThinkPlugin:
    stages = [PipelineStage.THINK]

    async def execute(self, context):
        context.set_stage_result("thought", True)


class RespondPlugin:
    stages = [PipelineStage.DO]

    async def execute(self, context):
        context.set_response("ok")


@pytest.mark.integration
def test_full_agent_pipeline():
    agent = Agent()
    agent.add_plugin(ParsePlugin())
    agent.add_plugin(ThinkPlugin())
    agent.add_plugin(RespondPlugin())

    result = asyncio.run(agent.handle("hi"))
    assert result["message"] == "ok"
    assert result["stage_results"].get("parsed") is True
    assert result["stage_results"].get("thought") is True
