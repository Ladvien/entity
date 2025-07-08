from __future__ import annotations

"""Pipeline component: utils."""

import logging
import time
from typing import Any, Awaitable, Callable

from ..metrics import MetricsCollector
from .tracing import start_span


async def execute_with_observability(
    func: Callable[..., Awaitable[Any]],
    logger: logging.Logger,
    metrics: MetricsCollector,
    plugin: str,
    stage: str,
    pipeline_id: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run ``func`` while logging and recording metrics."""
    logger.info(
        "Plugin execution started",
        extra={"plugin": plugin, "stage": stage, "pipeline_id": pipeline_id},
    )
    start = time.perf_counter()
    try:
        async with start_span(f"{stage}.{plugin}"):
            result = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        metrics.record_plugin_duration(plugin, stage, duration)
        logger.info(
            "Plugin execution finished",
            extra={
                "plugin": plugin,
                "stage": stage,
                "pipeline_id": pipeline_id,
                "duration": duration,
            },
        )
        return result
    except Exception as exc:
        logger.exception(
            "Plugin execution failed",
            extra={
                "plugin": plugin,
                "stage": stage,
                "pipeline_id": pipeline_id,
                "error": str(exc),
            },
        )
        raise
