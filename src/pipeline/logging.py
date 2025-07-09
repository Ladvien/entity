"""Logging utilities for the pipeline."""

from __future__ import annotations

"""Shims to maintain backward compatibility for logging utilities."""

from entity.utils.logging import configure_logging, get_logger


def set_request_id(request_id: str):  # pragma: no cover - compatibility stub
    return request_id


def reset_request_id(token: str) -> None:  # pragma: no cover - compatibility stub
    pass


__all__ = [
    "configure_logging",
    "get_logger",
    "set_request_id",
    "reset_request_id",
]
