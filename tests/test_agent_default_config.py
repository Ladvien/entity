import asyncio

from entity import Agent


def test_agent_no_config_runs_pipeline():
    agent = Agent()
    runtime = agent.builder.build_runtime()
    result = asyncio.run(runtime.run_pipeline("hello"))
    assert isinstance(result, dict)
    assert result.get("message")
