import asyncio

from entity import Agent


def test_agent_simple_config():
    agent = Agent(
        llm="pipeline.plugins.resources.echo_llm:EchoLLMResource",
        logging={
            "type": "pipeline.plugins.resources.structured_logging:StructuredLogging",
            "file_enabled": False,
        },
    )

    assert (
        agent.config["plugins"]["resources"]["ollama"]["type"]
        == "pipeline.plugins.resources.echo_llm:EchoLLMResource"
    )
    assert "logging" in agent.config["plugins"]["resources"]

    result = asyncio.run(agent.handle("hello"))
    assert isinstance(result, dict) and result.get("message")
