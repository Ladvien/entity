import asyncio

from entity import Agent


def test_agent_no_config_runs_pipeline():
    agent = Agent()
    result = asyncio.run(agent.handle("hello"))
    assert isinstance(result, dict)
    assert result.get("message")
