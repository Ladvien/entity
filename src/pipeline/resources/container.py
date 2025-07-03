from __future__ import annotations

from typing import Any, Dict, List

from registry.registries import ResourceRegistry


class ResourceContainer(ResourceRegistry):
    """Instantiate resources respecting declared dependencies."""

    def __init__(self) -> None:
        super().__init__()
        self._classes: Dict[str, type] = {}
        self._configs: Dict[str, Dict] = {}
        self._deps: Dict[str, List[str]] = {}
        self._order: List[str] = []

    def register(self, name: str, cls: type, config: Dict) -> None:
        self._classes[name] = cls
        self._configs[name] = config
        self._deps[name] = list(getattr(cls, "dependencies", []))

    async def build_all(self) -> None:
        self._order = self._resolve_order()
        for name in self._order:
            cls = self._classes[name]
            cfg = self._configs[name]
            instance = self._instantiate(cls, cfg)
            for dep in self._deps[name]:
                dep_obj = self.get(dep)
                if dep_obj is None:
                    raise SystemError(
                        f"Resource '{name}' requires '{dep}' which is missing"
                    )
                setattr(instance, dep, dep_obj)
            self.add(getattr(instance, "name", name), instance)
            init = getattr(instance, "initialize", None)
            if callable(init):
                await init()

    async def shutdown_all(self) -> None:
        for name in reversed(self._order):
            res = self.get(name)
            if res is None:
                continue
            shutdown = getattr(res, "shutdown", None)
            if callable(shutdown):
                await shutdown()

    async def health_report(self) -> Dict[str, bool]:
        report: Dict[str, bool] = {}
        for name in self._order:
            res = self.get(name)
            if res is None:
                continue
            func = getattr(res, "health_check", None)
            if func is None:
                report[name] = True
                continue
            try:
                report[name] = await func()
            except Exception:
                report[name] = False
        return report

    def _instantiate(self, cls: type, cfg: Dict) -> Any:
        if hasattr(cls, "from_config"):
            return cls.from_config(cfg)
        return cls(config=cfg)

    def _resolve_order(self) -> List[str]:
        in_degree = {n: 0 for n in self._deps}
        for node, deps in self._deps.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        queue = [n for n, d in in_degree.items() if d == 0]
        order: List[str] = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for dep in self._deps[current]:
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        if len(order) != len(in_degree):
            cycle = [n for n in in_degree if n not in order]
            raise SystemError(f"Circular dependency detected: {cycle}")
        return order
