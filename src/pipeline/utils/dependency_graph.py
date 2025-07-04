"""Dependency graph utilities for plugin ordering and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DependencyGraph:
    """Simple dependency graph with cycle detection."""

    graph: Dict[str, List[str]] = field(default_factory=dict)

    def _validate_missing(self) -> None:
        for node, deps in self.graph.items():
            for dep in deps:
                if dep not in self.graph:
                    available = list(self.graph)
                    raise SystemError(
                        f"Plugin '{node}' requires '{dep}' but it's not registered. "
                        f"Available: {available}"
                    )

    def topological_sort(self) -> List[str]:
        """Return nodes in dependency order or raise if a cycle exists."""
        self._validate_missing()

        in_degree: Dict[str, int] = {n: 0 for n in self.graph}
        for node, deps in self.graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue: List[str] = [n for n, d in in_degree.items() if d == 0]
        order: List[str] = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for dep in self.graph[current]:
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        if len(order) != len(in_degree):
            cycle = [n for n in in_degree if n not in order]
            raise SystemError(f"Circular dependency detected involving: {cycle}")

        return order


def topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """Convenience function returning dependency order."""
    return DependencyGraph(graph).topological_sort()
