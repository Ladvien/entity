from plugins.fun_fact_tool import FunFactTool, FunFactInput
import asyncio

tool = FunFactTool()


async def main():
    result = await tool.run(FunFactInput(topic="space"))
    print("✅ Output:", result)


asyncio.run(main())
