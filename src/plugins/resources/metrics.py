from __future__ import annotations

"""Prometheus metrics server resource."""

from typing import Dict

from pydantic import BaseModel, ValidationError

from pipeline.observability import MetricsServerManager
from pipeline.validation import ValidationResult
from plugins.resources.base import BaseResource


class MetricsResourceConfig(BaseModel):
    port: int = 9001


class MetricsResource(BaseResource):
    """Expose Prometheus metrics via an HTTP server."""

    name = "metrics"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        cfg = MetricsResourceConfig.model_validate(self.config)
        self._port = cfg.port

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        try:
            MetricsResourceConfig.model_validate(config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def initialize(self) -> None:
        """Initialize the metrics server if telemetry is enabled."""
        MetricsServerManager.start(self._port)

    def get_metrics(self) -> Dict[str, int]:
        return {"port": self._port}
