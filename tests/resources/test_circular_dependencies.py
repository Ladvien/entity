import pytest

from entity.core.resources.container import ResourceContainer
from entity.pipeline.errors import InitializationError
from entity.resources.base import AgentResource


def test_simple_dependency_cycle():
    class ResA(AgentResource):
        stages: list = []
        dependencies = ["b"]

    class ResB(AgentResource):
        stages: list = []
        dependencies = ["a"]

    container = ResourceContainer()
    container.register("a", ResA, {}, layer=4)
    container.register("b", ResB, {}, layer=4)

    with pytest.raises(InitializationError, match="Circular dependency detected"):
        container._resolve_order()


def test_longer_dependency_cycle():
    class ResA(AgentResource):
        stages: list = []
        dependencies = ["b"]

    class ResB(AgentResource):
        stages: list = []
        dependencies = ["c"]

    class ResC(AgentResource):
        stages: list = []
        dependencies = ["a"]

    container = ResourceContainer()
    container.register("a", ResA, {}, layer=4)
    container.register("b", ResB, {}, layer=4)
    container.register("c", ResC, {}, layer=4)

    with pytest.raises(InitializationError, match="Circular dependency detected"):
        container._resolve_order()
