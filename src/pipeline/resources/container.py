from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional


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


class ResourceContainer:
    """Container maintaining resources and optional pools."""

    def __init__(self) -> None:
        self._resources: Dict[str, Any] = {}
        self._pools: Dict[str, ResourcePool] = {}

    def add(self, name: str, resource: Any) -> None:
        self._resources[name] = resource

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
        self._resources[name] = pool

    async def acquire(self, name: str) -> Any:
        pool = self._pools.get(name)
        if pool is None:
            return self._resources.get(name)
        return await pool.acquire()

    async def release(self, name: str, resource: Any) -> None:
        pool = self._pools.get(name)
        if pool is not None:
            await pool.release(resource)

    def get_metrics(self) -> Dict[str, Dict[str, int]]:
        return {name: pool.metrics() for name, pool in self._pools.items()}
