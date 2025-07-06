from __future__ import annotations

"""Wrapper for PgVectorStore."""


def __getattr__(name: str):
    if name == "PgVectorStore":
        from plugins.builtin.resources.pg_vector_store import PgVectorStore

        return PgVectorStore
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PgVectorStore"]
