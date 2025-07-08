from __future__ import annotations

from typing import TYPE_CHECKING

"""Wrapper for PgVectorStore."""

# Defer import until used to avoid loading database drivers too early.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.pg_vector_store import PgVectorStore


def __getattr__(name: str):
    if name == "PgVectorStore":
        from plugins.builtin.resources.pg_vector_store import PgVectorStore

        return PgVectorStore
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PgVectorStore"]
