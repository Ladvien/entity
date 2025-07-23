from __future__ import annotations

from typing import Any, Dict, List


class MetricsCollectorResource:
    """Simple in-memory metrics collector."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []

    async def record_plugin_execution(
        self,
        plugin_name: str,
        stage: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        self.records.append(
            {
                "plugin_name": plugin_name,
                "stage": stage,
                "duration_ms": duration_ms,
                "success": success,
            }
        )
