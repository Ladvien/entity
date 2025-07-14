import asyncio
from entity import agent


@agent.output
async def echo(ctx):
    last = next(
        (e.content for e in reversed(ctx.conversation()) if e.role == "user"), ""
    )
    ctx.say(f"You said: {last}")


async def main() -> None:
    result = await agent.handle("Hello")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
