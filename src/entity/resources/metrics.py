from __future__ import annotations

import asyncio
import random
from typing import Any, Dict, List


class MetricsCollectorResource:
    """Collect and aggregate plugin execution metrics."""

    def __init__(self, sample_rate: float = 1.0) -> None:
        self.sample_rate = sample_rate
        self.records: List[Dict[str, Any]] = []
        self.aggregates: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def health_check(self) -> bool:
        """Return ``True`` as metrics collection has no external deps."""

        return True

    async def record_plugin_execution(
        self,
        plugin_name: str,
        stage: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record execution metrics for a plugin call."""

        if random.random() > self.sample_rate:
            return

        record = {
            "plugin_name": plugin_name,
            "stage": stage,
            "duration_ms": duration_ms,
            "success": success,
        }
        async with self._lock:
            self.records.append(record)
            key = f"{plugin_name}:{stage}"
            agg = self.aggregates.setdefault(
                key, {"count": 0, "success": 0, "duration_ms": 0.0}
            )
            agg["count"] += 1
            if success:
                agg["success"] += 1
            agg["duration_ms"] += duration_ms
