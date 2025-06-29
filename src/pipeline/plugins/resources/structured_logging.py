from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.stages import PipelineStage


class StructuredLogging(ResourcePlugin):
    """Configure Python's logging module based on YAML configuration."""

    stages = [PipelineStage.PARSE]
    name = "logging"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._configured = False

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

        level_name = str(self.config.get("level", "INFO")).upper()
        level = logging._nameToLevel.get(level_name, logging.INFO)
        fmt = self.config.get(
            "format", "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
        )

        handlers: list[logging.Handler] = [logging.StreamHandler()]
        if self.config.get("file_enabled"):
            file_path = str(self.config.get("file_path", "entity.log"))
            max_size = int(self.config.get("max_file_size", 10_485_760))
            backup_count = int(self.config.get("backup_count", 5))
            handlers.append(
                RotatingFileHandler(
                    file_path, maxBytes=max_size, backupCount=backup_count
                )
            )

        logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)
        self._configured = True

    async def initialize(self) -> None:
        self._configure_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _execute_impl(
        self, context
    ) -> Any:  # pragma: no cover - no runtime action
        return None
