import asyncio

from entity import agent
from entity.pipeline.pipeline import Pipeline
from entity.pipeline.stages import PipelineStage
from plugins.builtin.resources.ollama_llm import OllamaLLMResource
from entity.resources.logging import LoggingResource


@agent.tool
async def add(a: int, b: int) -> int:
    return a + b


@agent.output
async def final(ctx):
    result = await ctx.tool_use("add", a=1, b=1)
    ctx.say(str(result))


# Explicit workflow using the custom output plugin
agent.pipeline = Pipeline({PipelineStage.OUTPUT: ["final"]})


def test_agent_handle(monkeypatch):
    async def fake_generate(self, prompt: str):
        return "ok"

    monkeypatch.setattr(OllamaLLMResource, "generate", fake_generate, False)
    monkeypatch.setattr(LoggingResource, "dependencies", [], False)
    result = asyncio.run(agent.handle("hi"))
    assert result == "2"


def test_plugins_registered():
    assert agent.has_plugin("add")
    assert agent.has_plugin("final")
