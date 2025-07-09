class DependencyGraph:
    def __init__(self, graph):
        self.graph = graph

    def topological_sort(self):  # pragma: no cover - simple stub
        return list(self.graph)


__all__ = ["DependencyGraph"]
