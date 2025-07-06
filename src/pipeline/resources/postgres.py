from __future__ import annotations

"""Wrapper for PostgresResource."""


def __getattr__(name: str):
    if name == "PostgresResource":
        from plugins.builtin.resources.postgres import PostgresResource

        return PostgresResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["PostgresResource"]
