from __future__ import annotations

"""Centralized logging helpers for the pipeline."""

import contextvars
import json
import logging
<<<<<< codex/centralize-logging-and-integrate-tracing
import os
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Any, Optional
======
from importlib import import_module
<<<<<<< HEAD
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from plugins.builtin.adapters.logging_adapter import (
        JsonFormatter as _JsonFormatter,
    )  # noqa: F401,E501
    from plugins.builtin.adapters.logging_adapter import (
        RequestIdFilter as _RequestIdFilter,
    )  # noqa: F401,E501
=======
>>>>>>> c72003e014c664863289e303211be6661160fdc6


def _adapter():
    return import_module("plugins.builtin.adapters.logging_adapter")
>>>>>> main

__all__ = [
    "LogConfig",
    "LoggingConfigurator",
    "configure_logging",
    "get_logger",
    "set_request_id",
    "reset_request_id",
    "RequestIdFilter",
    "JsonFormatter",
]

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.request_id = _request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter used across the pipeline."""

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


@dataclass
class LogConfig:
    """Configuration parameters for the logger."""

    level: str = "INFO"
    json_enabled: bool = True
    file_enabled: bool = False
    file_path: Optional[str] = None
    max_file_size: int = 10_485_760
    backup_count: int = 5


class LoggingConfigurator:
    """Configure Python's logging for the pipeline."""

    def __init__(self, config: LogConfig | None = None) -> None:
        self.config = config or LogConfig()

    def configure(self) -> None:
        level = logging._nameToLevel.get(self.config.level.upper(), logging.INFO)
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        if self.config.file_enabled or os.getenv("ENTITY_LOG_PATH"):
            path = os.getenv("ENTITY_LOG_PATH") or self.config.file_path or "entity.log"
            handlers.append(
                RotatingFileHandler(
                    path,
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count,
                )
            )
        formatter: logging.Formatter = (
            JsonFormatter()
            if self.config.json_enabled
            else logging.Formatter("%(asctime)s [%(levelname)8s] %(name)s: %(message)s")
        )
        request_filter = RequestIdFilter()
        for handler in handlers:
            handler.setFormatter(formatter)
            handler.addFilter(request_filter)
        logging.basicConfig(level=level, handlers=handlers, force=True)


def configure_logging(**kwargs: Any) -> None:
    """Initialize logging using ``kwargs`` as :class:`LogConfig` fields."""

    LoggingConfigurator(LogConfig(**kwargs)).configure()


def get_logger(name: str) -> logging.Logger:
    """Return a logger preconfigured with the request ID filter."""

    logger = logging.getLogger(name)
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        logger.addFilter(RequestIdFilter())
    return logger


def set_request_id(request_id: str) -> contextvars.Token:
    """Store ``request_id`` for the duration of a log context."""

    return _request_id_var.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    """Reset the request ID context variable."""

    _request_id_var.reset(token)
