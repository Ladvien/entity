from __future__ import annotations

"""Demonstrate a multi-stage agent.

All resources are prepared automatically. Any initialization errors are
reported to the console.
"""

import asyncio

from entity.core.agent import Agent
from entity.defaults import DefaultConfig, load_defaults


class DummyLLM:
    async def generate(self, prompt: str) -> str:  # pragma: no cover - example
        return "dummy"


async def main() -> None:
    try:
        resources = load_defaults(DefaultConfig(auto_install_ollama=False))
    except Exception as exc:  # pragma: no cover - example runtime guard
        print(f"Failed to initialize resources: {exc}")
        return

    resources["llm"] = DummyLLM()
    agent = Agent.from_workflow("examples/advanced_workflow.yaml", resources=resources)
    result = await agent.chat("2 + 2")
    print(result["response"])


if __name__ == "__main__":
    asyncio.run(main())
