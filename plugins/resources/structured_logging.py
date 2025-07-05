from __future__ import annotations

"""Structured logging configuration resource."""
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict

from pipeline.validation import ValidationResult
from plugins.resources.base import BaseResource


class StructuredLogging(BaseResource):
    """Configure a unified JSON logger based on YAML configuration.

    Implements **Observable by Design (16)** by capturing structured logs for
    every pipeline execution. The optional ``ENTITY_LOG_PATH`` environment
    variable overrides ``file_path`` so multiple deployments can route logs to
    the same location.
    """

    name = "logging"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._configured = False

    class JsonFormatter(logging.Formatter):
        """Simple JSON log formatter."""

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

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        level = config.get("level")
        if level is not None and str(level).upper() not in logging._nameToLevel:
            return ValidationResult.error_result(f"Invalid log level: {level}")

        if config.get("file_enabled") and not config.get("file_path"):
            return ValidationResult.error_result(
                "'file_path' is required when file_enabled is True"
            )

        return ValidationResult.success_result()

    def _configure_logging(self) -> None:
        if self._configured:
            return

        level_name = str(self.config.get("level", "DEBUG")).upper()
        level = logging._nameToLevel.get(level_name, logging.DEBUG)

        json_enabled = self.config.get("json", True)

        fmt = self.config.get(
            "format",
            "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        )

        file_path_env = os.getenv("ENTITY_LOG_PATH")
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        if self.config.get("file_enabled") or file_path_env:
            file_path = file_path_env or str(self.config.get("file_path", "entity.log"))
            max_size = int(self.config.get("max_file_size", 10_485_760))
            backup_count = int(self.config.get("backup_count", 5))
            handlers.append(
                RotatingFileHandler(
                    file_path, maxBytes=max_size, backupCount=backup_count
                )
            )

        if json_enabled:
            formatter: logging.Formatter = self.JsonFormatter(fmt)
        else:
            formatter = logging.Formatter(fmt)

        for handler in handlers:
            handler.setFormatter(formatter)

        logging.basicConfig(level=level, handlers=handlers, force=True)
        self._configured = True

    async def initialize(self) -> None:
        self._configure_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
