import pytest

from entity.core.resources.container import DependencyGraph
from entity.pipeline.errors import InitializationError


def test_dependency_graph_cycle_detection():
    graph = {"a": ["b"], "b": ["a"]}
    dg = DependencyGraph(graph)
    with pytest.raises(InitializationError, match="Circular dependency detected"):
        dg.topological_sort()
