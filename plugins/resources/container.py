from __future__ import annotations

"""Asynchronous resource container."""
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from pipeline.utils import DependencyGraph
from registry.registries import ResourceRegistry


@dataclass
class PoolConfig:
    min_size: int = 1
    max_size: int = 5
    scale_threshold: float = 0.8
    scale_step: int = 1


class ResourcePool:
    """Asynchronous pool for expensive resources."""

    def __init__(
        self, factory: Callable[[], Awaitable[Any]], config: PoolConfig
    ) -> None:
        self._factory = factory
        self._cfg = config
        self._pool: asyncio.Queue[Any] = asyncio.Queue()
        self._total_size = 0
        self._lock = asyncio.Lock()
        self._ctx_resource: Any | None = None

    async def initialize(self) -> None:
        for _ in range(self._cfg.min_size):
            await self._grow()

    async def _grow(self) -> None:
        if self._total_size >= self._cfg.max_size:
            return
        resource = await self._factory()
        await self._pool.put(resource)
        self._total_size += 1

    def _utilization(self) -> float:
        if self._total_size == 0:
            return 0.0
        in_use = self._total_size - self._pool.qsize()
        return in_use / self._total_size

    async def acquire(self) -> Any:
        async with self._lock:
            if self._pool.empty() and self._total_size < self._cfg.max_size:
                await self._grow()
            resource = await self._pool.get()
            if (
                self._utilization() > self._cfg.scale_threshold
                and self._total_size < self._cfg.max_size
            ):
                for _ in range(
                    min(self._cfg.scale_step, self._cfg.max_size - self._total_size)
                ):
                    await self._grow()
            return resource

    async def release(self, resource: Any) -> None:
        async with self._lock:
            await self._pool.put(resource)

    def metrics(self) -> Dict[str, int]:
        return {
            "total_size": self._total_size,
            "in_use": self._total_size - self._pool.qsize(),
            "available": self._pool.qsize(),
        }

    async def __aenter__(self) -> Any:
        self._ctx_resource = await self.acquire()
        return self._ctx_resource

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._ctx_resource is not None:
            await self.release(self._ctx_resource)
            self._ctx_resource = None


class ResourceContainer(ResourceRegistry):
    """Instantiate resources with dependency injection and optional pools."""

    def __init__(self) -> None:
        super().__init__()
        self._classes: Dict[str, type] = {}
        self._configs: Dict[str, Dict] = {}
        self._deps: Dict[str, List[str]] = {}
        self._order: List[str] = []
        self._pools: Dict[str, ResourcePool] = {}

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

    async def add_pool(
        self,
        name: str,
        factory: Callable[[], Awaitable[Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        cfg = PoolConfig(**(config or {}))
        pool = ResourcePool(factory, cfg)
        await pool.initialize()
        self._pools[name] = pool
        super().add(name, pool)

    async def acquire(self, name: str) -> Any:
        pool = self._pools.get(name)
        if pool is not None:
            return await pool.acquire()
        return self.get(name)

    async def release(self, name: str, resource: Any) -> None:
        pool = self._pools.get(name)
        if pool is not None:
            await pool.release(resource)

    def get_metrics(self) -> Dict[str, Dict[str, int]]:
        return {name: pool.metrics() for name, pool in self._pools.items()}

    async def __aenter__(self) -> "ResourceContainer":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown_all()

    def _instantiate(self, cls: type, cfg: Dict) -> Any:
        if hasattr(cls, "from_config"):
            return cls.from_config(cfg)
        return cls(config=cfg)

    def _resolve_order(self) -> List[str]:
        # Build dependency graph with edges from each dependency to its dependents
        graph_map: Dict[str, List[str]] = {name: [] for name in self._deps}
        for name, deps in self._deps.items():
            for dep in deps:
                graph_map.setdefault(dep, []).append(name)
        graph = DependencyGraph(graph_map)
        return graph.topological_sort()
