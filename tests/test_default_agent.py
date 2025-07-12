import asyncio

from entity import agent
from plugins.builtin.resources.ollama_llm import OllamaLLMResource


@agent.tool
async def add(a: int, b: int) -> int:
    return a + b


@agent.prompt
async def final(ctx):
    result = await ctx.tool_use("add", a=1, b=1)
    ctx.say(str(result))


def test_agent_handle(monkeypatch):
    async def fake_generate(self, prompt: str):
        return "ok"

    monkeypatch.setattr(OllamaLLMResource, "generate", fake_generate, False)
    result = asyncio.run(agent.handle("hi"))
    assert result["message"] == "hi"


def test_plugins_registered():
    assert agent.builder.has_plugin("add")
    assert agent.builder.has_plugin("final")
