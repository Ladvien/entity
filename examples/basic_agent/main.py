import asyncio
import sys
from pathlib import Path

# Ensure this example can find the entity package when run directly
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

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
