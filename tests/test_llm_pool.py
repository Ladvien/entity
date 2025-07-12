import asyncio
import sys
import types

import pytest

sys.modules.setdefault(
    "plugins.builtin.resources.duckdb_resource", types.ModuleType("duckdb_resource")
)

from entity.core.resources.container import ResourceContainer
from entity.resources.llm import LLM
from entity.resources.interfaces.llm import LLMResource


class DummyProvider(LLMResource):
    def __init__(self) -> None:
        super().__init__({})
        self.calls: list[str] = []

    async def generate(self, prompt: str):
        self.calls.append(prompt)
        await asyncio.sleep(0.01)
        return prompt


@pytest.mark.asyncio
async def test_llm_pool_metrics():
    provider = DummyProvider()
    llm = LLM({"pool": {"min_size": 1, "max_size": 2}})
    llm.provider = provider
    await llm.initialize()

    container = ResourceContainer()
    await container.add("llm", llm)

    await asyncio.gather(*(llm.generate(str(i)) for i in range(3)))

    metrics = container.get_metrics()
    assert metrics["llm"]["total_size"] >= 1
    assert len(provider.calls) == 3
