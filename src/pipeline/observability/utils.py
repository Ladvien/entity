from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable

from ..metrics import MetricsCollector


async def execute_with_observability(
    func: Callable[..., Awaitable[Any]],
    logger: logging.Logger,
    metrics: MetricsCollector,
    plugin: str,
    stage: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run ``func`` while logging and recording metrics."""
    logger.info(
        "Plugin execution started",
        extra={"plugin": plugin, "stage": stage},
    )
    start = time.perf_counter()
    try:
        result = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        metrics.record_plugin_duration(plugin, stage, duration)
        logger.info(
            "Plugin execution finished",
            extra={"plugin": plugin, "stage": stage, "duration": duration},
        )
        return result
    except Exception as exc:
        logger.exception(
            "Plugin execution failed",
            extra={"plugin": plugin, "stage": stage, "error": str(exc)},
        )
        raise
