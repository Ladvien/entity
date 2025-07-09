"""Lightweight logging helpers."""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a standard library logger."""

    return logging.getLogger(name)
