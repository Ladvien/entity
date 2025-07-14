import asyncio
from entity import agent
from entity.core.stages import PipelineStage
from user_plugins.responders import ComplexPromptResponder


@agent.prompt(stage=PipelineStage.THINK)
async def chain_of_thought(ctx):
    user = next((e.content for e in ctx.conversation() if e.role == "user"), "")
    await ctx.think("complex_response", f"Problem breakdown: {user}")


async def main() -> None:
    await agent.add_plugin(ComplexPromptResponder({}))
    result = await agent.handle("Explain the sky")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
