"""Asynchronous resource container."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar

from entity.pipeline.errors import InitializationError


class DependencyGraph:
    def __init__(self, graph: Dict[str, List[str]]) -> None:
        self.graph = graph

    def topological_sort(self) -> List[str]:
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
            for dep in self.graph.get(current, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        if len(order) != len(in_degree):
            cycle_nodes = [n for n in in_degree if n not in order]
            nodes = ", ".join(sorted(cycle_nodes))
            raise InitializationError(
                "dependency graph",
                "order resolution",
                f"Circular dependency detected among: {nodes}",
                kind="Resource",
            )
        return order


@dataclass
class PoolConfig:
    min_size: int = 1
    max_size: int = 5
    scale_threshold: float = 0.8
    scale_step: int = 1


T = TypeVar("T")


class ResourcePool(Generic[T]):
    """Asynchronous pool for expensive resources."""

    def __init__(
        self, factory: Callable[[], Awaitable[T] | T], config: PoolConfig
    ) -> None:
        self._factory = factory
        self._cfg = config
        self._pool: asyncio.Queue[T] = asyncio.Queue()
        self._total_size = 0
        self._lock = asyncio.Lock()
        self._ctx_resource: T | None = None

    async def initialize(self) -> None:
        for _ in range(self._cfg.min_size):
            await self._grow()

    async def _grow(self) -> None:
        if self._total_size >= self._cfg.max_size:
            return
        result = self._factory()
        resource = await result if asyncio.iscoroutine(result) else result
        await self._pool.put(resource)
        self._total_size += 1

    def _utilization(self) -> float:
        if self._total_size == 0:
            return 0.0
        in_use = self._total_size - self._pool.qsize()
        return in_use / self._total_size

    async def acquire(self) -> T:
        async with self._lock:
            if self._pool.empty() and self._total_size < self._cfg.max_size:
                await self._grow()
        resource = await self._pool.get()
        async with self._lock:
            if (
                self._utilization() > self._cfg.scale_threshold
                and self._total_size < self._cfg.max_size
            ):
                for _ in range(
                    min(self._cfg.scale_step, self._cfg.max_size - self._total_size)
                ):
                    await self._grow()
        return resource

    async def release(self, resource: T) -> None:
        async with self._lock:
            await self._pool.put(resource)

    def metrics(self) -> Dict[str, int]:
        return {
            "total_size": self._total_size,
            "in_use": self._total_size - self._pool.qsize(),
            "available": self._pool.qsize(),
        }

    async def __aenter__(self) -> T:
        self._ctx_resource = await self.acquire()
        return self._ctx_resource

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._ctx_resource is not None:
            await self.release(self._ctx_resource)
            self._ctx_resource = None


class ResourceContainer:
    """Instantiate resources with dependency injection and optional pools.

    Declare dependencies on resource classes via the ``dependencies`` class
    attribute. Append ``?`` to a dependency name to mark it as optional. Missing
    optional dependencies are injected as ``None`` instead of raising an error.
    """

    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._classes: Dict[str, type] = {}
        self._configs: Dict[str, Dict] = {}
        self._deps: Dict[str, List[str]] = {}
        self._layers: Dict[str, int] = {}
        self._order: List[str] = []
        self._init_order: List[str] = []
        self._pools: Dict[str, ResourcePool] = {}

    async def add(self, name: str, resource: Any) -> None:
        async with self._lock:
            self._resources[name] = resource

    async def add_from_config(self, name: str, cls: type, config: Dict) -> None:
        instance = self._create_instance(cls, config)
        await self.add(name, instance)

    def get(self, name: str) -> Any | None:
        return self._resources.get(name)

    def has_plugin(self, name: str) -> bool:
        """Return ``True`` if a resource with ``name`` is registered."""

        return name in self._classes or name in self._resources

    async def remove(self, name: str) -> None:
        async with self._lock:
            self._resources.pop(name, None)

    async def __aenter__(self) -> "ResourceContainer":
        for resource in self._resources.values():
            init = getattr(resource, "initialize", None)
            if callable(init):
                await init()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        for resource in self._resources.values():
            shutdown = getattr(resource, "shutdown", None)
            if callable(shutdown):
                await shutdown()

    def register(
        self, name: str, cls: type, config: Dict, layer: int | None = None
    ) -> None:
        """Register a resource class and its configuration."""

        from entity.core.plugins import InfrastructurePlugin, ResourcePlugin

        if layer is None:
            from entity.resources.base import AgentResource as CanonicalResource

            if issubclass(cls, InfrastructurePlugin):
                layer = 1
            elif issubclass(cls, ResourcePlugin):
                layer = 2
            elif issubclass(cls, CanonicalResource):
                layer = 3
            else:
                layer = 4

        self._classes[name] = cls
        clean_cfg = {
            k: v
            for k, v in config.items()
            if k not in {"type", "dependencies", "stage", "stages"}
        }
        self._configs[name] = clean_cfg
        deps = list(getattr(cls, "dependencies", []))
        if issubclass(cls, ResourcePlugin):
            deps.extend(getattr(cls, "infrastructure_dependencies", []))
        self._deps[name] = deps
        self._layers[name] = layer

    async def build_all(self) -> None:
        """Instantiate and initialize resources in layer order."""
        if "logging" not in self._classes and "logging" not in self._resources:
            from entity.resources.logging import LoggingResource

            self.register("logging", LoggingResource, {}, layer=3)

        self._validate_layers()
        self._order = self._resolve_order()
        self._init_order = []

        for name in self._order:
            cls = self._classes[name]
            cfg = self._configs[name]

            result = cls.validate_config(cfg)
            if asyncio.iscoroutine(result):
                result = await result
            if not result.success:
                raise InitializationError(
                    name,
                    "config validation",
                    f"{result.message}. Fix the resource configuration.",
                    kind="Resource",
                )

            dep_result = cls.validate_dependencies(self)
            if asyncio.iscoroutine(dep_result):
                dep_result = await dep_result
            if not dep_result.success:
                raise InitializationError(
                    name,
                    "dependency validation",
                    f"{dep_result.message}. Fix the resource dependencies.",
                    kind="Resource",
                )

            instance = self._create_instance(cls, cfg)
            await self.add(name, instance)

            self._inject_dependencies(name, instance)

            init = getattr(instance, "initialize", None)
            if callable(init):
                await init()
            self._init_order.append(name)

            check = getattr(instance, "health_check", None)
            if callable(check) and not await check():
                raise InitializationError(
                    name,
                    "health check",
                    "Resource failed health check during initialization.",
                    kind="Resource",
                )

    async def shutdown_all(self) -> None:
        order = self._init_order or self._order
        for name in reversed(order):
            res = self.get(name)
            if res is None:
                continue
            check = getattr(res, "health_check", None)
            if callable(check) and not await check():
                await self._restart_resource(name)
                res = self.get(name)
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
        factory: Callable[[], Awaitable[Any] | Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        cfg = PoolConfig(**(config or {}))
        pool = ResourcePool(factory, cfg)
        await pool.initialize()
        self._pools[name] = pool
        await self.add(name, pool)

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
        metrics = {name: pool.metrics() for name, pool in self._pools.items()}
        for name, resource in self._resources.items():
            getter = getattr(resource, "get_pool_metrics", None)
            if callable(getter):
                metrics[name] = getter()
        return metrics

    def _create_instance(self, cls: type, cfg: Dict) -> Any:
        if hasattr(cls, "from_config"):
            return cls.from_config(cfg)
        return cls(config=cfg)

    def _dependents(self, name: str) -> List[str]:
        deps: List[str] = []
        for res, dep_list in self._deps.items():
            for dep in dep_list:
                dep_name = dep[:-1] if dep.endswith("?") else dep
                if dep_name == name:
                    deps.append(res)
        return deps

    async def _restart_resource(self, name: str) -> bool:
        old = self.get(name)
        if old is not None:
            shutdown = getattr(old, "shutdown", None)
            if callable(shutdown):
                try:
                    await shutdown()
                except Exception:
                    pass
        cls = self._classes.get(name)
        cfg = self._configs.get(name)
        if cls is None or cfg is None:
            return False
        instance = self._create_instance(cls, cfg)
        await self.add(name, instance)
        self._inject_dependencies(name, instance)
        for dep in self._dependents(name):
            dep_inst = self.get(dep)
            if dep_inst is not None:
                self._inject_dependencies(dep, dep_inst)
        init = getattr(instance, "initialize", None)
        if callable(init):
            await init()
        check = getattr(instance, "health_check", None)
        if callable(check):
            return await check()
        return True

    async def restart_failed(self) -> None:
        report = await self.health_report()
        for name, ok in report.items():
            if not ok:
                await self._restart_resource(name)

    def _inject_dependencies(self, name: str, instance: Any) -> None:
        """Attach dependencies to ``instance``.

        Dependencies ending with ``?`` are optional and will be injected as
        ``None`` when absent. Required dependencies raise ``SystemError`` if
        missing.
        """

        for dep in self._deps.get(name, []):
            optional = dep.endswith("?")
            dep_name = dep[:-1] if optional else dep
            dep_obj = self.get(dep_name)
            if dep_obj is None and not optional:
                raise InitializationError(
                    name,
                    "dependency injection",
                    f"Required dependency '{dep_name}' is missing.",
                    kind="Resource",
                )
            setattr(instance, dep_name, dep_obj)

    def _dependencies_satisfied(self, name: str) -> bool:
        """Return ``True`` if all required deps for ``name`` exist."""
        for dep in self._deps.get(name, []):
            optional = dep.endswith("?")
            dep_name = dep[:-1] if optional else dep
            if dep_name not in self._resources and not optional:
                return False
        return True

    def _validate_layers(self) -> None:
        """Ensure layer dependencies follow the 4-layer architecture."""

        from entity.core.plugins import (
            AgentResource as PluginAgentResource,
            InfrastructurePlugin,
            ResourcePlugin,
        )
        from entity.resources.base import AgentResource as CanonicalResource

        for name, layer in self._layers.items():
            if layer not in {1, 2, 3, 4}:
                raise InitializationError(
                    name,
                    "layer validation",
                    f"Invalid layer {layer} specified.",
                    kind="Resource",
                )
            cls = self._classes[name]

            is_infra = issubclass(cls, InfrastructurePlugin)
            is_interface = issubclass(cls, ResourcePlugin)
            is_canonical = issubclass(cls, (CanonicalResource, PluginAgentResource))

            expected = (
                1 if is_infra else 2 if is_interface else 3 if is_canonical else 4
            )

            if layer != expected:
                message = (
                    f"Provided layer {layer} for {cls.__name__} is invalid."
                    if expected == 3
                    else f"Incorrect layer {layer} for {cls.__name__}. Expected {expected}."
                )
                raise InitializationError(
                    name, "layer validation", message, kind="Resource"
                )

            if is_infra:
                if self._deps.get(name):
                    raise InitializationError(
                        name,
                        "layer validation",
                        "Infrastructure resources cannot have dependencies.",
                        kind="Resource",
                    )
                if not getattr(cls, "infrastructure_type", ""):
                    raise InitializationError(
                        name,
                        "layer validation",
                        "Infrastructure resource missing infrastructure_type.",
                        kind="Resource",
                    )

            if (
                is_interface
                and not is_canonical
                and not getattr(cls, "infrastructure_dependencies", None)
            ):
                raise InitializationError(
                    name,
                    "layer validation",
                    "Resource interface must declare infrastructure_dependencies.",
                    kind="Resource",
                )

        for name, deps in self._deps.items():
            for dep in deps:
                optional = dep.endswith("?")
                dep_name = dep[:-1] if optional else dep
                dep_layer = self._layers.get(dep_name)
                if dep_layer is None:
                    if optional:
                        continue
                    raise InitializationError(
                        name,
                        "layer validation",
                        f"Resource depends on '{dep_name}' but it is not registered.",
                        kind="Resource",
                    )
                if self._layers[name] - dep_layer != 1:
                    raise InitializationError(
                        name,
                        "layer validation",
                        f"Resource depends on '{dep_name}' and violates layer rules.",
                        kind="Resource",
                    )

    def _resolve_order(self) -> List[str]:
        # Build dependency graph with edges from each dependency to its dependents
        graph_map: Dict[str, List[str]] = {name: [] for name in self._deps}
        for name, deps in self._deps.items():
            for dep in deps:
                dep_name = dep[:-1] if dep.endswith("?") else dep
                if dep_name in graph_map:
                    graph_map[dep_name].append(name)
        graph = DependencyGraph(graph_map)
        try:
            return graph.topological_sort()
        except InitializationError as exc:
            raise InitializationError(
                ", ".join(sorted(graph_map.keys())),
                "dependency graph",
                str(exc),
                kind="Resource",
            ) from exc
