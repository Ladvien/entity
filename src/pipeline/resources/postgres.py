from __future__ import annotations

"""Pipeline component: postgres."""

from typing import TYPE_CHECKING

"""Wrapper for PostgresResource."""

# Delays import so psycopg and friends load only when needed.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.postgres import PostgresResource


def __getattr__(name: str):
    if name == "PostgresResource":
        from plugins.builtin.resources.postgres import PostgresResource

        return PostgresResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PostgresResource"]
