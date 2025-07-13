# ruff: noqa: E402
import asyncio
import sys
import types

import pytest

sys.modules.setdefault(
    "entity.resources.interfaces.duckdb_resource", types.ModuleType("duckdb_resource")
)

from entity.core.resources.container import ResourceContainer
from entity.resources.llm import LLM
from entity.resources.interfaces.llm import LLMResource
from entity.resources.metrics import MetricsCollectorResource


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


class UnstableProvider(LLMResource):
    def __init__(self) -> None:
        super().__init__({})
        self.healthy = True

    async def generate(self, prompt: str):
        return prompt

    async def health_check(self) -> bool:
        return self.healthy

    async def restart(self) -> None:
        self.healthy = True


@pytest.mark.asyncio
async def test_pool_recovers_unhealthy_resource():
    provider = UnstableProvider()
    metrics = MetricsCollectorResource({})
    llm = LLM({"pool": {"min_size": 1, "max_size": 2}})
    llm.provider = provider
    llm.metrics_collector = metrics
    await llm.initialize()

    async with llm.get_client_pool() as _:
        provider.healthy = False

    async with llm.get_client_pool() as _:
        pass

    assert provider.healthy


@pytest.mark.asyncio
async def test_pool_scales_with_load():
    provider = DummyProvider()
    metrics = MetricsCollectorResource({})
    llm = LLM({"pool": {"min_size": 1, "max_size": 3, "scale_threshold": 0.5}})
    llm.provider = provider
    llm.metrics_collector = metrics
    await llm.initialize()

    async def call(i: int) -> None:
        await llm.generate(str(i))

    await asyncio.gather(*(call(i) for i in range(4)))

    pool_metrics = llm.get_pool_metrics()
    assert pool_metrics["total_size"] > 1
