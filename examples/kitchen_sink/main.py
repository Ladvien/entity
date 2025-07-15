import sys
from pathlib import Path

# Ensure this example can find the entity package when run directly
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from entity import agent, prompt
from user_plugins.tools.calculator_tool import CalculatorTool
from user_plugins.responders import ReactResponder


@prompt
async def react_prompt(ctx):
    question = next((e.content for e in ctx.conversation() if e.role == "user"), "")
    tool_result = await ctx.tool_use("calc", expression="2+2")
    thoughts = await ctx.reflect("react_thoughts", [])
    thoughts.append(f"Thinking about {question} using tool result {tool_result}")
    await ctx.think("react_thoughts", thoughts)


async def main() -> None:
    await agent.builder.tool_registry.add("calc", CalculatorTool())
    await agent.add_plugin(ReactResponder({}))
    result = await agent.handle("What is 2 + 2?")
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
