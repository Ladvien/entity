from __future__ import annotations

"""Adapter wrapper exposing logging configuration helpers."""

from pipeline.base_plugins import AdapterPlugin
from pipeline.logging import (
    JsonFormatter,
    LoggingConfigurator,
    RequestIdFilter,
    configure_logging,
    get_logger,
    reset_request_id,
    set_request_id,
)
from pipeline.stages import PipelineStage

__all__ = [
    "LoggingAdapter",
    "RequestIdFilter",
    "JsonFormatter",
    "configure_logging",
    "get_logger",
    "set_request_id",
    "reset_request_id",
    "LoggingConfigurator",
]


class LoggingAdapter(AdapterPlugin):
    """Adapter placeholder for logging setup."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
