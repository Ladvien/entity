from __future__ import annotations

"""Resource definition DSL used by the container."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

try:
    import graphviz
except Exception:  # pragma: no cover - optional dependency
    graphviz = None


@dataclass
class ResourceDef:
    """Definition of a resource within the DSL."""

    name: str
    type: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


class ResourceGraph:
    """Collection of :class:`ResourceDef` objects with validation helpers."""

    def __init__(self) -> None:
        self._resources: Dict[str, ResourceDef] = {}

    # --- DSL methods -----------------------------------------------------
    def resource(
        self,
        name: str,
        *,
        type: str,
        config: Dict[str, Any] | None = None,
        depends_on: List[str] | None = None,
    ) -> None:
        if name in self._resources:
            raise ValueError(f"Resource '{name}' already defined")
        self._resources[name] = ResourceDef(
            name=name,
            type=type,
            config=config or {},
            dependencies=depends_on or [],
        )

    # --- Parsing ---------------------------------------------------------
    @classmethod
    def from_dict(cls, cfg: Dict[str, Dict[str, Any]]) -> "ResourceGraph":
        graph = cls()
        for name, node in cfg.items():
            if not isinstance(node, dict):
                raise ValueError(f"Resource '{name}' must map to a dictionary")
            deps = node.get("depends_on", [])
            if deps is not None and not isinstance(deps, list):
                raise ValueError(f"'depends_on' for '{name}' must be a list")
            graph.resource(
                name,
                type=node.get("type", name),
                config={
                    k: v for k, v in node.items() if k not in {"type", "depends_on"}
                },
                depends_on=deps or [],
            )
        graph.validate()
        return graph

    # --- Validation ------------------------------------------------------
    def validate(self) -> None:
        for res in self._resources.values():
            for dep in res.dependencies:
                if dep not in self._resources:
                    raise ValueError(
                        f"Resource '{res.name}' depends on unknown resource '{dep}'"
                    )
        self._topological_order()

    def _topological_order(self) -> List[str]:
        in_degree: Dict[str, int] = {name: 0 for name in self._resources}
        children: Dict[str, List[str]] = {name: [] for name in self._resources}
        for name, res in self._resources.items():
            for dep in res.dependencies:
                children[dep].append(name)
                in_degree[name] += 1
        queue = [n for n, d in in_degree.items() if d == 0]
        processed: List[str] = []
        while queue:
            current = queue.pop(0)
            processed.append(current)
            for child in children[current]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        if len(processed) != len(self._resources):
            cycle = [n for n in self._resources if n not in processed]
            raise ValueError(f"Circular dependency detected: {cycle}")
        return processed

    # --- Graph Visualization --------------------------------------------
    def to_dot(self) -> str:
        lines = ["digraph resources {"]
        for name, res in self._resources.items():
            if not res.dependencies:
                lines.append(f'    "{name}";')
            for dep in res.dependencies:
                lines.append(f'    "{dep}" -> "{name}";')
        lines.append("}")
        return "\n".join(lines)

    def to_graphviz(self) -> "graphviz.Digraph":  # pragma: no cover - optional
        if graphviz is None:
            raise RuntimeError("graphviz package not installed")
        dot = graphviz.Digraph("resources")
        for name, res in self._resources.items():
            dot.node(name)
            for dep in res.dependencies:
                dot.edge(dep, name)
        return dot

    # --- Convenience accessors -----------------------------------------
    @property
    def resources(self) -> Dict[str, ResourceDef]:
        return dict(self._resources)
