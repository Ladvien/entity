from __future__ import annotations

"""Minimal logging helpers used across the project."""

import logging
from logging import Logger


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with a simple format."""
    level_name = level.upper()
    log_level = logging._nameToLevel.get(level_name, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )


def get_logger(name: str) -> Logger:
    """Return a logger instance."""
    return logging.getLogger(name)


__all__ = ["configure_logging", "get_logger"]
