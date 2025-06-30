import asyncio

from entity import Agent
from pipeline import PipelineStage


def test_agent_plugin_autoclassification():
    agent = Agent()

    @agent.plugin
    async def think_response(context):
        return "thinking"

    @agent.plugin(stage=PipelineStage.PARSE)
    async def parse_func(context):
        return "parsed"

    think_plugins = agent.plugins.get_for_stage(PipelineStage.THINK)
    parse_plugins = agent.plugins.get_for_stage(PipelineStage.PARSE)

    assert any(p.name == "think_response" for p in think_plugins)
    assert any(p.name == "parse_func" for p in parse_plugins)

    result = asyncio.run(agent.run_message("hi"))
    assert result == "parsed"
