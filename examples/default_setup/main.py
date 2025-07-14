import sys
from pathlib import Path

# Ensure this example can find the entity package when run directly
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from entity import agent, output, tool


@tool
async def add(a: int, b: int) -> int:
    return a + b


@output
async def responder(ctx):
    user = next((e.content for e in ctx.conversation() if e.role == "user"), "")
    result = await ctx.tool_use("add", a=2, b=2)
    ctx.say(f"{user} -> {result}")


async def main() -> None:
    response = await agent.handle("hello")
    print(response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
