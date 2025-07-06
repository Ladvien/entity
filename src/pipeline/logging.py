"""Logging utilities for the pipeline."""

from __future__ import annotations


def configure_logging(*args, **kwargs):
    from plugins.builtin.adapters.logging_adapter import configure_logging

    return configure_logging(*args, **kwargs)


def get_logger(name: str):
    from plugins.builtin.adapters.logging_adapter import get_logger

    return get_logger(name)


def set_request_id(request_id: str):
    from plugins.builtin.adapters.logging_adapter import set_request_id

    return set_request_id(request_id)


def reset_request_id(token):
    from plugins.builtin.adapters.logging_adapter import reset_request_id

    return reset_request_id(token)


__all__ = [
    "configure_logging",
    "get_logger",
    "set_request_id",
    "reset_request_id",
]
