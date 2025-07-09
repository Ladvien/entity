import asyncio

from pipeline import Agent, PipelineStage


def test_agent_plugin_autoclassification():
    agent = Agent()

    @agent.plugin
    async def think_response(context):
        return "thinking"

    @agent.plugin(stage=PipelineStage.PARSE)
    async def parse_func(context):
        return "parsed"

    think_plugins = agent.plugins.get_plugins_for_stage(PipelineStage.THINK)
    parse_plugins = agent.plugins.get_plugins_for_stage(PipelineStage.PARSE)

    assert any(p.name == "think_response" for p in think_plugins)
    assert any(p.name == "parse_func" for p in parse_plugins)

    agent._runtime = agent.builder.build_runtime()
    result = asyncio.run(agent.run_message("hi"))
    assert result == "parsed"
