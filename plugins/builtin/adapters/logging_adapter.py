from __future__ import annotations

"""Logging utilities packaged as an adapter plugin."""

import contextvars
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from pipeline.base_plugins import AdapterPlugin
from pipeline.stages import PipelineStage

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.request_id = _request_id_var.get()
        return True


def set_request_id(request_id: str) -> contextvars.Token:
    """Store ``request_id`` for the duration of a log context."""

    return _request_id_var.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    """Reset the request ID context variable."""

    _request_id_var.reset(token)


class JsonFormatter(logging.Formatter):
    """Basic JSON log formatter used across the pipeline."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }
        }
        log_record.update(extras)
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def configure_logging(
    level: str = "INFO",
    json_enabled: bool = True,
    file_enabled: bool = False,
    file_path: Optional[str] = None,
    max_file_size: int = 10_485_760,
    backup_count: int = 5,
) -> None:
    """Configure a root logger for the pipeline."""

    level_name = level.upper()
    log_level = logging._nameToLevel.get(level_name, logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if file_enabled or os.getenv("ENTITY_LOG_PATH"):
        path = os.getenv("ENTITY_LOG_PATH") or file_path or "entity.log"
        handlers.append(
            RotatingFileHandler(path, maxBytes=max_file_size, backupCount=backup_count)
        )
    formatter: logging.Formatter = (
        JsonFormatter()
        if json_enabled
        else logging.Formatter("%(asctime)s [%(levelname)8s] %(name)s: %(message)s")
    )
    request_filter = RequestIdFilter()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(request_filter)
    logging.basicConfig(level=log_level, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for the pipeline."""

    logger = logging.getLogger(name)
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        logger.addFilter(RequestIdFilter())
    return logger


class LoggingAdapter(AdapterPlugin):
    """Adapter placeholder for logging setup."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass


__all__ = [
    "LoggingAdapter",
    "RequestIdFilter",
    "JsonFormatter",
    "configure_logging",
    "get_logger",
    "set_request_id",
    "reset_request_id",
]
