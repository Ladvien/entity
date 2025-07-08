from __future__ import annotations

"""Prototype async resource registry. Not production ready."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict

from plugins.resources.base import BaseResource


@dataclass
class ManagerMetrics:
    """Simple metrics for the resource manager."""

    resources_registered: int = 0
    resources_initialized: int = 0
    health_checks: int = 0
    health_failures: int = 0
    init_durations: Dict[str, float] = field(default_factory=dict)


class AsyncResourceManager:
    """Asynchronous registry and lifecycle manager for resources."""

    def __init__(self) -> None:
        self._resources: Dict[str, BaseResource] = {}
        self.metrics = ManagerMetrics()
        self._lock = asyncio.Lock()

    async def register(self, name: str, resource: BaseResource) -> None:
        async with self._lock:
            self._resources[name] = resource
            self.metrics.resources_registered += 1

    def get(self, name: str) -> BaseResource | None:
        return self._resources.get(name)

    async def initialize_all(self) -> None:
        for name, resource in self._resources.items():
            start = time.perf_counter()
            await resource.initialize()
            duration = time.perf_counter() - start
            self.metrics.resources_initialized += 1
            self.metrics.init_durations[name] = duration

    async def shutdown_all(self) -> None:
        for resource in self._resources.values():
            await resource.shutdown()

    async def health_report(self) -> Dict[str, bool]:
        report: Dict[str, bool] = {}
        for name, resource in self._resources.items():
            try:
                healthy = await resource.health_check()
            except Exception:
                healthy = False
            if not healthy:
                self.metrics.health_failures += 1
            self.metrics.health_checks += 1
            report[name] = healthy
        return report


__all__ = ["AsyncResourceManager", "BaseResource", "ManagerMetrics"]
