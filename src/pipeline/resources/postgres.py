from __future__ import annotations

from typing import TYPE_CHECKING

"""Wrapper for PostgresResource."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.postgres import PostgresResource


def __getattr__(name: str):
    if name == "PostgresResource":
        from plugins.builtin.resources.postgres import PostgresResource

        return PostgresResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PostgresResource"]
