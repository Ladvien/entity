from __future__ import annotations

import json
import logging

from .state import MetricsCollector

logger = logging.getLogger(__name__)


def log_metrics(metrics: MetricsCollector) -> None:
    """Log collected metrics using the standard logger."""

    data = metrics.to_dict()
    logger.info("Pipeline metrics", extra={"metrics": data})


def metrics_as_json(metrics: MetricsCollector) -> str:
    """Return metrics as a formatted JSON string."""

    return json.dumps(metrics.to_dict(), indent=2)
