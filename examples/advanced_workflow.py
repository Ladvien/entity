from __future__ import annotations

import asyncio

from entity.core.agent import Agent
from entity.defaults import load_defaults


class DummyLLM:
    async def generate(self, prompt: str) -> str:  # pragma: no cover - example
        return "dummy"


async def main() -> None:
    resources = load_defaults()
    resources["llm"] = DummyLLM()
    agent = Agent.from_workflow("examples/advanced_workflow.yaml", resources=resources)
    result = await agent.chat("2 + 2")
    print(result["response"])


if __name__ == "__main__":
    asyncio.run(main())
