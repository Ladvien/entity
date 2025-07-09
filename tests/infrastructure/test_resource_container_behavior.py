import asyncio
from typing import List

import pytest

from pipeline.resources import ResourceContainer
from common_interfaces.resources import BaseResource


class A(BaseResource):
    async def initialize(self) -> None:
        events.append("a")


class B(BaseResource):
    dependencies = ["a"]

    async def initialize(self) -> None:
        events.append("b")


class Failing(BaseResource):
    dependencies = ["b"]

    async def initialize(self) -> None:
        events.append("f")

    async def health_check(self) -> bool:
        return False


class C(BaseResource):
    dependencies = ["f"]

    async def initialize(self) -> None:
        events.append("c")


events: List[str] = []


@pytest.mark.asyncio
async def test_build_all_dependency_order() -> None:
    events.clear()
    container = ResourceContainer()
    container.register("a", A, {})
    container.register("b", B, {})
    await container.build_all()
    assert events == ["a", "b"]


@pytest.mark.asyncio
async def test_build_all_stops_on_failure() -> None:
    events.clear()
    container = ResourceContainer()
    container.register("a", A, {})
    container.register("b", B, {})
    container.register("f", Failing, {})
    container.register("c", C, {})
    with pytest.raises(SystemError):
        await container.build_all()
    assert events == ["a", "b", "f"]
    assert container.get("c") is None


@pytest.mark.asyncio
async def test_shutdown_all_reverse_order() -> None:
    log: list[str] = []

    class R1(BaseResource):
        async def initialize(self) -> None:
            log.append("i1")

        async def shutdown(self) -> None:
            log.append("s1")

    class R2(BaseResource):
        dependencies = ["r1"]

        async def initialize(self) -> None:
            log.append("i2")

        async def shutdown(self) -> None:
            log.append("s2")

    container = ResourceContainer()
    container.register("r1", R1, {})
    container.register("r2", R2, {})
    await container.build_all()
    await container.shutdown_all()
    assert log == ["i1", "i2", "s2", "s1"]
