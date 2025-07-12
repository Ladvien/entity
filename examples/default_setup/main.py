import asyncio

from entity import Agent
from entity.resources.memory import Memory
from entity.pipeline.stages import PipelineStage


@agent.tool
async def add(a: int, b: int) -> int:
    return a + b


@agent.prompt(stage=PipelineStage.OUTPUT)
async def responder(ctx):
    user = next((e.content for e in ctx.conversation() if e.role == "user"), "")
    result = await ctx.tool_use("add", a=2, b=2)
    ctx.say(f"{user} -> {result}")


async def main() -> None:
    response = await agent.handle("hello")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
