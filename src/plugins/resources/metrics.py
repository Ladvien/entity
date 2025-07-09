from __future__ import annotations

"""Prometheus metrics server resource."""

from typing import Dict

from pipeline.observability import MetricsServerManager
from pipeline.validation import ValidationResult
from plugins.resources.base import BaseResource


class MetricsResource(BaseResource):
    """Expose Prometheus metrics via an HTTP server."""

    name = "metrics"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._port = int(self.config.get("port", 9001))

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        try:
            int(config.get("port", 9001))
        except Exception:
            return ValidationResult.error_result("'port' must be an integer")
        return ValidationResult.success_result()

    async def initialize(self) -> None:
        MetricsServerManager.start(self._port)

    def get_metrics(self) -> Dict[str, int]:
        return {"port": self._port}
