from __future__ import annotations

"""Re-export logging helpers from :class:`LoggingAdapter`."""

import contextvars
import logging
from importlib import import_module


def _adapter():
    return import_module("plugins.builtin.adapters.logging_adapter")


def configure_logging(*args, **kwargs):
    return _adapter().configure_logging(*args, **kwargs)


def get_logger(name: str) -> logging.Logger:
    return _adapter().get_logger(name)


def set_request_id(request_id: str) -> contextvars.Token:
    return _adapter().set_request_id(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    _adapter().reset_request_id(token)


def RequestIdFilter(*args, **kwargs):  # type: ignore[override]
    return _adapter().RequestIdFilter(*args, **kwargs)


def JsonFormatter(*args, **kwargs):  # type: ignore[override]
    return _adapter().JsonFormatter(*args, **kwargs)


class LoggingAdapter:  # pragma: no cover - compatibility stub
    pass


__all__ = [
    "RequestIdFilter",
    "JsonFormatter",
    "configure_logging",
    "get_logger",
    "set_request_id",
    "reset_request_id",
    "LoggingAdapter",
]
