from __future__ import annotations

"""Demonstrate a complex vLLM setup with manual resource wiring."""

import asyncio
import os

from entity import Agent
from entity.defaults import load_defaults
from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.resources import LLMResource, LLM


async def main() -> None:
    try:
        os.environ.setdefault("ENTITY_JSON_LOGS", "1")
        os.environ.setdefault("ENTITY_LOG_LEVEL", "debug")
        os.environ.setdefault("ENTITY_LOG_FILE", "kitchen.log")

        # Launch vLLM with a specific model and GPU utilization
        vllm = VLLMInfrastructure(
            model="Qwen/Qwen2.5-7B-Instruct",
            gpu_memory_utilization=0.8,
        )
        resources = load_defaults()
        resources["llm"] = LLM(LLMResource(vllm))
    except Exception as exc:  # pragma: no cover - example runtime guard
        print(f"Resource setup failed: {exc}")
        return

    agent = Agent(resources=resources)
    await agent.chat("ping")


if __name__ == "__main__":
    asyncio.run(main())
